import pytest

from app.models import PriceChange
from app.tests.conftest import MockResponse
from applifting.tasks import update_offers_for_products_in_db

pytestmark = pytest.mark.django_db


class TestTask:
    mocked_offer_response = [
        {"id": "404f6aad-89a3-9397-4947-3ffb01b57ddd", "price": 75152, "items_in_stock": 931},
        {"id": "241149f4-efa4-931b-0dcf-ff4228db5a06", "price": 72950, "items_in_stock": 411},
        {"id": "509ac030-b5c9-d4e8-1aff-e1953a4946a4", "price": 77718, "items_in_stock": 716},
    ]

    def test_update_offers_for_products_in_db(
        self, api_client, mocked_service_auth, product_factory, offer_factory, price_change_factory, mocker
    ):
        # mocking offer response
        response_mock = mocker.patch("applifting.tasks.service_request_get")
        response_mock.return_value = MockResponse(self.mocked_offer_response, 200)
        product = product_factory()
        offer_1 = offer_factory(product=product, id="404f6aad-89a3-9397-4947-3ffb01b57ddd")
        price_change_factory(offer=offer_1)
        offer_2 = offer_factory(product=product)
        price_change_factory(offer=offer_2)
        update_offers_for_products_in_db()
        product.refresh_from_db()
        assert product.offers.count() == 4
        offer_1.refresh_from_db()
        assert offer_1.price == 75152
        assert offer_1.items_in_stock == 931
        assert offer_1.active is True
        assert offer_1.price_changes.count() == 2
        assert offer_1.price_changes.last().price == 75152
        offer_2.refresh_from_db()
        assert offer_2.active is False
        assert offer_2.price_changes.count() == 1
        assert PriceChange.objects.count() == 5
