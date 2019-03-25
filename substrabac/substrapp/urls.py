"""
substrapp URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from substrapp.views import ObjectiveViewSet, DataViewSet, DataManagerViewSet, \
    AlgoViewSet, TrainTupleViewSet, TestTupleViewSet, ModelViewSet, TaskViewSet

# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r'objective', ObjectiveViewSet, base_name='objective')
router.register(r'model', ModelViewSet, base_name='model')
router.register(r'data', DataViewSet, base_name='data')
router.register(r'datamanger', DataManagerViewSet, base_name='data_manger')
router.register(r'algo', AlgoViewSet, base_name='algo')
router.register(r'traintuple', TrainTupleViewSet, base_name='traintuple')
router.register(r'testtuple', TestTupleViewSet, base_name='testtuple')
router.register(r'task', TaskViewSet, base_name='task')

urlpatterns = [
    url(r'^', include(router.urls)),
]
