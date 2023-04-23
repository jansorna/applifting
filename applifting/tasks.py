import logging

from app.helpers.applifting_api import product_api
from app.models import Product
from .celery import celery_app


logger = logging.getLogger(__name__)


@celery_app.task()
def update_offers_for_products_in_db():
    """
    Synchronizes offers from offer service. Creates new offers, updates active offers, deactivates sold out offers and
    create price changes.
    """
    logger.info("Syncing offers from offer service.")
    products = Product.objects.all().prefetch_related("offers")
    product_api.sync_products_offers(products)
