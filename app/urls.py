from django.urls import path
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

from app.views import ProductViewSet, OfferViewSet

router = routers.DefaultRouter(trailing_slash=False)

router.register("product", ProductViewSet, basename="product")
router.register("offer", OfferViewSet, basename="offer")

urlpatterns = [path("api-token-auth/", obtain_auth_token, name="api_token_auth")] + router.urls
