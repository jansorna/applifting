import pytest
from django.urls import reverse

from app.models import Product
from app.tests.conftest import MockResponse

pytestmark = pytest.mark.django_db


class TestProduct:
    list_endpoint = reverse("product-list")
    mocked_offer_response = [
        {"id": "404f6aad-89a3-9397-4947-3ffb01b57ddd", "price": 75152, "items_in_stock": 931},
        {"id": "241149f4-efa4-931b-0dcf-ff4228db5a06", "price": 72950, "items_in_stock": 411},
        {"id": "509ac030-b5c9-d4e8-1aff-e1953a4946a4", "price": 77718, "items_in_stock": 716},
    ]

    def test_list(self, api_client, product_factory):
        product_factory.create_batch(5)
        response = api_client.get(self.list_endpoint)
        assert response.status_code == 200
        assert len(response.json().get("results")) == 5
        for product_data in response.json().get("results"):
            assert set(product_data.keys()) == {"created_date", "description", "id", "name", "updated_date"}

    def test_detail(self, api_client, product_factory, offer_factory):
        product = product_factory()
        offer_factory(product=product)
        detail_url = reverse("product-detail", args=(str(product.id),))
        response = api_client.get(detail_url)
        assert response.status_code == 200
        assert response.json().get("id") == str(product.id)
        assert set(response.json().keys()) == {"created_date", "description", "id", "name", "offers", "updated_date"}
        for offers_data in response.json().get("offers"):
            assert set(offers_data.keys()) == {
                "active",
                "created_date",
                "id",
                "items_in_stock",
                "price",
                "product",
                "updated_date",
            }

    def test_post(self, api_client, mocked_service_auth, mocked_product_register, mocker):
        # mocking offer response
        response_mock = mocker.patch("app.models.service_request_get")
        response_mock.return_value = MockResponse(self.mocked_offer_response, 200)

        data = {
            "name": "Product",
            "description": "Description of product.",
        }
        response = api_client.post(self.list_endpoint, data=data, format="json")
        assert response.status_code == 201
        for field_name, value in data.items():
            assert response.json().get(field_name) == value
        product = Product.objects.get(id=response.json().get("id"))
        assert product.offers.count() == 3

    def test_update(self, api_client, product_factory):
        product = product_factory()
        detail_url = reverse("product-detail", args=(str(product.id),))
        data = {
            "description": "Updated description of product.",
        }
        response = api_client.patch(detail_url, data=data, format="json")
        assert response.status_code == 200
        for field_name, value in data.items():
            assert response.json().get(field_name) == value
