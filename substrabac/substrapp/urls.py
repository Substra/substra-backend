"""
substrapp URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from substrapp.views import ProblemViewSet, DataViewSet, DataOpenerViewSet, AlgoViewSet, LearnupletViewSet

# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r'problem', ProblemViewSet, base_name='problem')
router.register(r'data', DataViewSet, base_name='data')
router.register(r'dataopener', DataOpenerViewSet, base_name='dataopener')
router.register(r'algo', AlgoViewSet, base_name='algo')
router.register(r'learnuplet', LearnupletViewSet, base_name='algo')


urlpatterns = [
    url(r'^', include(router.urls)),
]
