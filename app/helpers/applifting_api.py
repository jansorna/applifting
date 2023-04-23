import os
import logging
from datetime import datetime
from typing import List

import jwt
import requests
import urllib3
from django.conf import settings
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter

from app.models import Product, Offer, PriceChange

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 10


class AppLiftingAPI:
    """
    Wrapper for general API calls to provided Applifting API.
    """

    def __init__(self):
        self.sign_on_token = os.getenv("SIGN_UP_TOKEN", None)
        self.token_refresh_endpoint = os.getenv("AUTH_SERVICE_URL", "https://python.exercise.applifting.cz/api/v1/auth")

    def _get_service_token(self):
        """
        Gets service token from sign on token.
        Write it to .env_local_dev.
        Set service token to env var.
        """
        retry_session = self._requests_retry_session(retries=6, backoff_factor=0.5)
        call = getattr(retry_session, "post")
        logger.info("Requesting Bearer token from Auth server.")
        response = call(url=self.token_refresh_endpoint, headers={"Bearer": self.sign_on_token}, timeout=5)
        if response.status_code != 201:
            logger.warning(
                f"Auth service return unexpected result. status_code: {response.status_code}, "
                f"json: {response.json()}"
            )
        response.raise_for_status()
        access_token = response.json().get("access_token")
        # write service token to .env_local_dev
        with open(".env_local_dev", "r", encoding="UTF-8") as orig:
            past_lines = orig.readlines()
            future_lines = [line for line in past_lines if "SERVICE_TOKEN" not in line]
        with open(".env_local_dev", "w", encoding="UTF-8") as overwrite:
            future_lines.append(f"SERVICE_TOKEN={access_token}\n")
            overwrite.writelines(future_lines)
        # set new token to env var
        os.environ["SERVICE_TOKEN"] = access_token
        return access_token

    def _get_refreshed_service_access_token(self):
        """
        Returns refreshed token.
        """
        load_dotenv(verbose=True, dotenv_path=os.path.join(settings.BASE_DIR, ".env_local_dev"))
        access_token = os.getenv("SERVICE_TOKEN", None)
        if not access_token:
            access_token = self._get_service_token()
        decoded_token = jwt.decode(access_token, options={"verify_signature": False}, algorithms=["RS256"])
        if datetime.fromtimestamp(decoded_token["expires"]) <= datetime.now():
            access_token = self._get_service_token()
        return access_token

    def _requests_retry_session(
        self,
        retries=3,
        backoff_factor=0.3,
    ):
        session = requests.Session()
        retry = urllib3.Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=(500, 502, 503, 504),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _service_request(
        self,
        service,
        endpoint,
        method,
        json_data=None,
        timeout=DEFAULT_TIMEOUT,
        params=None,
    ):
        if method not in ("get", "post"):
            raise ValueError("unsupported method")

        retry_session = self._requests_retry_session()
        call = getattr(retry_session, method)

        service_url = os.getenv(f"{service.upper()}_SERVICE_URL", "https://python.exercise.applifting.cz")
        headers = {"Bearer": f"{self._get_refreshed_service_access_token()}"}

        if service_url.endswith("/") and endpoint.startswith("/"):
            endpoint = endpoint[1:]
        url = f"{service_url}{endpoint}"
        logger.info(f"Sending {method} request to {url}.")
        response = call(url=url, headers=headers, json=json_data, timeout=timeout, params=params)
        if response.status_code >= 400:
            logger.warning(f"{method} request failed, {response.status_code} {response.reason}")
        return response

    def service_request_get(self, service, endpoint, timeout=DEFAULT_TIMEOUT, params=None):
        return self._service_request(service, endpoint, "get", None, timeout, params)

    def service_request_post(
        self,
        service,
        endpoint,
        json_data=None,
        timeout=DEFAULT_TIMEOUT,
        params=None,
    ):
        return self._service_request(service, endpoint, "post", json_data, timeout, params)


class ProductAPI(AppLiftingAPI):
    """
    Wrapper for API calls for Product objects.
    """

    def _get_offers_for_product(self, product: Product):
        response = self.service_request_get("offer", f"/products/{product.id}/offers")
        if response.status_code != 200:
            logger.warning(
                f"Offer service return unexpected result. status_code: {response.status_code}, "
                f"json: {response.json()}"
            )
        response.raise_for_status()
        return response

    def register_product(self, product: Product):
        """
        Register product in provided Applifting API.
        """
        response = self.service_request_post(
            service="offer",
            endpoint="/products/register",
            json_data={"id": str(product.id), "name": product.name, "description": product.description},
        )
        response.raise_for_status()

    def sync_products_offers(self, products: List[Product]):
        """
        Fetch all offers of products in database from provided Applifting API.
        Sync theirs offers(price, items_in_stock).
        Also make PriceChange objects if offer is created/changed.
        """
        new_offers = []
        update_offers = []
        price_change = []
        for product in products:
            response = self._get_offers_for_product(product)
            active_product_offers_in_db = list(product.offers.filter(active=True))
            active_offers_ids_in_db = set(str(offer.id) for offer in active_product_offers_in_db)
            active_offers_ids_in_offer_service = set(offer["id"] for offer in response.json())
            # update offers in db
            for active_offer in active_product_offers_in_db:
                # deactivate not active
                if str(active_offer.id) not in active_offers_ids_in_offer_service:
                    active_offer.active = False
                    update_offers.append(active_offer)
                # update active offers
                else:
                    offer_to_update = [offer for offer in response.json() if offer["id"] == str(active_offer.id)][0]
                    price_change.append(
                        PriceChange(
                            price=offer_to_update["price"],
                            offer=active_offer,
                        )
                    )
                    active_offer.price = offer_to_update["price"]
                    active_offer.items_in_stock = offer_to_update["items_in_stock"]
                    update_offers.append(active_offer)
            # create new offers
            for new_offer in response.json():
                if new_offer["id"] not in active_offers_ids_in_db:
                    new_offers.append(
                        Offer(
                            id=new_offer["id"],
                            price=new_offer["price"],
                            items_in_stock=new_offer["items_in_stock"],
                            product=product,
                        )
                    )
                    price_change.append(
                        PriceChange(
                            price=new_offer["price"],
                            offer_id=new_offer["id"],
                        )
                    )

        if new_offers:
            logger.info(f"Creating {len(new_offers)} offers.")
            Offer.objects.bulk_create(new_offers)
        if update_offers:
            logger.info(f"Updating {len(update_offers)} offers.")
            Offer.objects.bulk_update(update_offers, ["price", "items_in_stock", "active"])
        if price_change:
            logger.info(f"Creating {len(price_change)} price changes.")
            PriceChange.objects.bulk_create(price_change)


product_api = ProductAPI()
