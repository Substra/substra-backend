"""
substrapp URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from substrapp.views import ChallengeViewSet, DataViewSet, DatasetViewSet, \
    AlgoViewSet, TrainTupleViewSet, TestTupleViewSet, ModelViewSet, TaskViewSet

# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r'challenge', ChallengeViewSet, base_name='challenge')
router.register(r'model', ModelViewSet, base_name='model')
router.register(r'data', DataViewSet, base_name='data')
router.register(r'dataset', DatasetViewSet, base_name='dataset')
router.register(r'algo', AlgoViewSet, base_name='algo')
router.register(r'traintuple', TrainTupleViewSet, base_name='traintuple')
router.register(r'testtuple', TestTupleViewSet, base_name='testtuple')
router.register(r'task', TaskViewSet, base_name='task')

urlpatterns = [
    url(r'^', include(router.urls)),
]
