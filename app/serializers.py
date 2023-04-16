from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app.models import Product, Offer


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"
        read_only_field = ("id", "price", "items_in_stock")


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_field = ("id",)

    @transaction.atomic()
    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.register_product_in_offer_service()
        instance.create_offers_for_product()
        return instance


class OfferDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Offer
        fields = ("id", "price", "items_in_stock", "product", "created_date", "updated_date")
        read_only_field = ("id", "price", "items_in_stock", "product", "created_date", "updated_field")


class ProductDetailSerializer(serializers.ModelSerializer):
    offers = OfferSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "description", "offers", "created_date", "updated_date")
        read_only_field = ("id",)


class DatetimePeriodSerializer(serializers.Serializer):
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()

    def validate(self, attrs):
        if attrs["period_start"] >= attrs["period_end"]:
            raise ValidationError({"detail": "period_start must be before period_end"})
        return attrs
