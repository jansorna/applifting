from django.dispatch import receiver
from django.db.models.signals import post_save
from app.helpers.applifting_api import product_api
from app.models import Product


@receiver(post_save, sender=Product)
def register_product_and_create_offers(sender, instance, **kwargs):
    product_api.register_product(instance)
    product_api.sync_products_offers([instance])
