"""
substrapp URL
"""

from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it.
from users.views import AuthenticationViewSet
from users.views import UserViewSet

router = DefaultRouter()
router.register(r"me", AuthenticationViewSet, basename="me")
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
]
