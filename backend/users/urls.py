"""
substrapp URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it.
from users.views import UserViewSet

router = DefaultRouter()
router.register(r'user', UserViewSet, basename='user')

urlpatterns = [
    url(r'^', include(router.urls)),
]
