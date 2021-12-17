"""
node URL
"""

from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from node.views import NodeViewSet

# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r"node", NodeViewSet, basename="node")

urlpatterns = [
    path("", include(router.urls)),
]
