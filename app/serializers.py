from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app.helpers.applifting_api import product_api
from app.models import Product, Offer


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"


class OfferForProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        exclude = ("product",)


class ProductSerializer(serializers.ModelSerializer):
    offers = OfferForProductSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = "__all__"
        read_only_field = ("id", "created_date", "updated_date")

    @transaction.atomic()
    def create(self, validated_data):
        instance = super().create(validated_data)
        product_api.register_product(instance)
        product_api.sync_products_offers([instance])
        return instance


class DatetimePeriodSerializer(serializers.Serializer):
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()

    def validate(self, attrs):
        if attrs["period_start"] >= attrs["period_end"]:
            raise ValidationError({"detail": "period_start must be before period_end"})
        return attrs
