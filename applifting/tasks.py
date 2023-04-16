import logging

from django.db.models import Prefetch

from app.helpers.service_request import service_request_get
from app.models import Product, Offer, PriceChange
from .celery import celery_app


logger = logging.getLogger(__name__)


@celery_app.task()
def update_offers_for_products_in_db():
    """
    Synchronizes offers from offer service. Creates new offers, updates active offers, deactivates sold out offers and
    create price changes.
    """
    logger.info("Syncing offers from offer service.")
    products = Product.objects.all().prefetch_related(
        Prefetch("offers", queryset=Offer.objects.filter(active=True), to_attr="active_offers")
    )
    new_offers = []
    update_offers = []
    price_change = []
    for product in products:
        response = service_request_get("offer", f"/products/{product.id}/offers")
        if response.status_code == 200:
            active_offers_ids_in_db = set(str(offer.id) for offer in product.active_offers)
            active_offers_ids_in_offer_service = set(offer["id"] for offer in response.json())
            # update offers in db
            for active_offer in product.active_offers:
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
        else:
            logger.warning(
                f"Offer service return unexpected result. status_code: {response.status_code}, "
                f"json: {response.json()}"
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
