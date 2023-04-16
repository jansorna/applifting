import uuid

from django.db import models

from app.helpers.service_request import service_request_post, service_request_get


class TimeStampedModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(TimeStampedModel):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()

    def register_product_in_offer_service(self):
        response = service_request_post(
            service="offer",
            endpoint="/products/register",
            json_data={"id": str(self.id), "name": self.name, "description": self.description},
        )
        response.raise_for_status()

    def create_offers_for_product(self):
        response = service_request_get("offer", f"/products/{self.id}/offers")
        response.raise_for_status()
        offers = []
        price_change = []
        if response.status_code == 200:
            for new_offer in response.json():
                offers.append(
                    Offer(
                        id=new_offer["id"],
                        price=new_offer["price"],
                        items_in_stock=new_offer["items_in_stock"],
                        product=self,
                    )
                )
                price_change.append(
                    PriceChange(
                        price=new_offer["price"],
                        offer_id=new_offer["id"],
                    )
                )
            if offers:
                Offer.objects.bulk_create(offers)
            if price_change:
                PriceChange.objects.bulk_create(price_change)


class Offer(TimeStampedModel):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    price = models.PositiveIntegerField()
    items_in_stock = models.PositiveIntegerField()
    product = models.ForeignKey(Product, to_field="id", related_name="offers", on_delete=models.CASCADE)
    active = models.BooleanField(default=True)


class PriceChange(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    price = models.PositiveIntegerField()
    offer = models.ForeignKey(Offer, to_field="id", related_name="price_changes", on_delete=models.CASCADE)
