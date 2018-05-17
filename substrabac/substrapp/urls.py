"""
substrapp URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from substrapp.views import ProblemViewSet, DataViewSet, DataOpenerViewSet


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'problem', ProblemViewSet, base_name='problem')
router.register(r'data', DataViewSet, base_name='data')
router.register(r'dataopener', DataOpenerViewSet, base_name='dataopener')


urlpatterns = [
    url(r'^', include(router.urls)),
]
