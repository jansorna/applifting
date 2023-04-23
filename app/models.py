import uuid

from django.db import models


class TimeStampedModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(TimeStampedModel):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()


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
