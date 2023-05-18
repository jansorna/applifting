from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from app.enums import TrendType
from app.models import Product, Offer
from app.serializers import (
    ProductSerializer,
    OfferSerializer,
    DatetimePeriodSerializer,
)


class ProductViewSet(ModelViewSet):
    lookup_field = "id"
    permission_classes = (AllowAny | IsAuthenticated,)
    serializer_class = ProductSerializer

    def get_queryset(self):
        if self.action == "retrieve":
            return Product.objects.all().prefetch_related("offers")
        else:
            return Product.objects.all()


class OfferViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    lookup_field = "id"
    permission_classes = (AllowAny | IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "price_history":
            return DatetimePeriodSerializer
        else:
            return OfferSerializer

    def get_queryset(self):
        if self.action == "retrieve":
            return Offer.objects.filter(active=True).select_related("product")
        elif self.action == "price_history":
            return Offer.objects.all().prefetch_related("price_changes")
        else:
            return Offer.objects.filter(active=True)

    @action(detail=True, methods=["post"])
    def price_history(self, request, *args, **kwargs):
        offer = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        period_start = serializer.validated_data["period_start"]
        period_end = serializer.validated_data["period_end"]
        prices = offer.price_changes.filter(created_date__gte=period_start, created_date__lte=period_end).order_by(
            "created_date"
        )
        if len(prices) >= 2:
            first_price_change = prices.first()
            last_price_change = prices.last()
            percentage_change = last_price_change.price / first_price_change.price
            if percentage_change > 1:
                data = {"trend": TrendType.INCREASING}
            elif percentage_change < 1:
                data = {"trend": TrendType.DECREASING}
            else:
                data = {"trend": TrendType.STAGNATING}
            data["percentage_change"] = str(round((percentage_change - 1) * 100, 2)) + "%"
            return Response(status=200, data=data)
        else:
            return Response(status=200, data={"In provided period offer price was not changed."})
