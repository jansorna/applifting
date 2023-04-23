import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestOffer:
    list_endpoint = reverse("offer-list")

    def test_list(self, api_client, offer_factory):
        offer_factory.create_batch(5)
        response = api_client.get(self.list_endpoint)
        assert response.status_code == 200
        assert len(response.json().get("results")) == 5
        for product_data in response.json().get("results"):
            assert set(product_data.keys()) == {
                "id",
                "price",
                "items_in_stock",
                "product",
                "active",
                "created_date",
                "updated_date",
            }

    def test_detail(self, api_client, product_factory, offer_factory):
        product = product_factory()
        offer = offer_factory(product=product)
        detail_url = reverse("offer-detail", args=(str(offer.id),))
        response = api_client.get(detail_url)
        assert response.status_code == 200
        assert response.json().get("id") == str(offer.id)
        assert set(response.json().keys()) == {
            "created_date",
            "id",
            "items_in_stock",
            "price",
            "product",
            "updated_date",
            "active",
        }

    def test_price_history(self, api_client, product_factory, offer_factory, price_change_factory):
        product = product_factory()
        offer = offer_factory(product=product)
        price_change_factory(offer=offer, price=100)
        price_change_factory(offer=offer, price=102)
        price_history_url = reverse("offer-price-history", args=(str(offer.id),))
        data = {
            "period_start": "2020-01-01T00:00:00.00+00:00",
            "period_end": "2025-01-01T00:00:00.00+00:00",
        }
        response = api_client.post(price_history_url, data=data)
        assert response.status_code == 200
        assert response.json() == {"percentage_change": "2.0%", "trend": "increasing"}
