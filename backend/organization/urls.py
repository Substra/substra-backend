"""
organization URL
"""

from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from organization.views import OrganizationViewSet

# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r"organization", OrganizationViewSet, basename="organization")

urlpatterns = [
    path("", include(router.urls)),
]
