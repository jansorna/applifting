import pytest

from pytest_factoryboy import register
from app.tests.factories import ProductFactory, OfferFactory, PriceChangeFactory


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        pass


# register factories
register(ProductFactory)
register(OfferFactory)
register(PriceChangeFactory)


# fixtures
# noqa pylint:disable=C0415
@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def mocked_service_auth(requests_mock):
    requests_mock.post(
        "https://python.exercise.applifting.cz/api/v1/auth",
        json={
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbiI6IjQ0MzRhOTk2LTQzO"
            "WMtNDdkYy1iYzg3LTA1NDBkNThiNjNlMiIsImV4cGlyZXMiOjE2ODE2NTQ4NDl9.nxXgfFSZtUfF10E5JS"
            "UVh7g2kdQyyVZiRWP3UbKN7fc"
        },
    )


@pytest.fixture
def mocked_product_register(requests_mock):
    requests_mock.post("https://python.exercise.applifting.cz/api/v1/products/register", json={})
