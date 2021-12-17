"""
substrapp URL
"""

from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it.
from users.views import UserViewSet

router = DefaultRouter()
router.register(r"user", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
