import factory

from app.models import Product, Offer, PriceChange


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    id = factory.Faker("uuid4")
    name = factory.Faker("name")
    description = factory.Faker("sentence")


class OfferFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Offer

    id = factory.Faker("uuid4")
    price = factory.Faker("pyint", min_value=1, max_value=99999)
    items_in_stock = factory.Faker("pyint", min_value=0, max_value=999)
    product = factory.SubFactory(ProductFactory)


class PriceChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PriceChange

    price = factory.Faker("pyint", min_value=1, max_value=99999)
    offer = factory.SubFactory(OfferFactory)
