import os
import logging
from datetime import datetime

import jwt
import requests
import urllib3
from django.conf import settings
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 10


def _get_service_token():
    """
    Gets service token from sign on token.
    """
    token_refresh_endpoint = os.getenv("AUTH_SERVICE_URL", "https://python.exercise.applifting.cz/api/v1/auth")
    sign_on_token = os.getenv("SIGN_UP_TOKEN", "sign_up_token")
    retry_session = _requests_retry_session(retries=6, backoff_factor=0.5)
    call = getattr(retry_session, "post")
    logger.info("Requesting Bearer token from Auth server.")
    response = call(url=token_refresh_endpoint, headers={"Bearer": sign_on_token}, timeout=5)
    response.raise_for_status()
    return response.json()


def _get_refreshed_service_access_token():
    """
    Returns refreshed token which can be used for requests on offer service.
    """
    access_token = settings.SERVICE_TOKEN
    if not access_token:
        settings.SERVICE_TOKEN = _get_service_token()
        print(settings.SERVICE_TOKEN)
        access_token = settings.SERVICE_TOKEN
    decoded_token = jwt.decode(access_token["access_token"], options={"verify_signature": False}, algorithms=["RS256"])
    if datetime.fromtimestamp(decoded_token["expires"]) <= datetime.now():
        settings.SERVICE_TOKEN = _get_service_token()
    return settings.SERVICE_TOKEN["access_token"]


def _requests_retry_session(
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
    service,
    endpoint,
    method,
    json_data=None,
    timeout=DEFAULT_TIMEOUT,
    params=None,
):
    if method not in ("get", "post"):
        raise ValueError("unsupported method")

    retry_session = _requests_retry_session()
    call = getattr(retry_session, method)

    service_url = os.getenv(f"{service.upper()}_SERVICE_URL", "https://python.exercise.applifting.cz")
    headers = {"Bearer": f"{_get_refreshed_service_access_token()}"}

    if service_url.endswith("/") and endpoint.startswith("/"):
        endpoint = endpoint[1:]
    url = f"{service_url}{endpoint}"
    logger.info(f"Sending {method} request to {url}.")
    response = call(url=url, headers=headers, json=json_data, timeout=timeout, params=params)
    if response.status_code >= 400:
        logger.warning(f"{method} request failed, {response.status_code} {response.reason}")
    return response


def service_request_get(service, endpoint, timeout=DEFAULT_TIMEOUT, params=None):
    return _service_request(service, endpoint, "get", None, timeout, params)


def service_request_post(
    service,
    endpoint,
    json_data=None,
    timeout=DEFAULT_TIMEOUT,
    params=None,
):
    return _service_request(service, endpoint, "post", json_data, timeout, params)
