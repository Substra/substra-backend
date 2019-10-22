"""
node URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from node.views import NodeViewSet

# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r'node', NodeViewSet, base_name='node')

urlpatterns = [
    url(r'^', include(router.urls)),
]
