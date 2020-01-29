"""
substrapp URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from substrapp.views import ObjectiveViewSet, DataSampleViewSet, DataManagerViewSet, \
    AlgoViewSet, TrainTupleViewSet, TestTupleViewSet, ModelViewSet, TaskViewSet, \
    ComputePlanViewSet, ObjectivePermissionViewSet, AlgoPermissionViewSet, DataManagerPermissionViewSet, \
    ModelPermissionViewSet, CompositeTraintupleViewSet, CompositeAlgoViewSet, CompositeAlgoPermissionViewSet, \
    AggregateAlgoViewSet, AggregateAlgoPermissionViewSet, AggregateTupleViewSet


# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r'objective', ObjectiveViewSet, basename='objective')
router.register(r'objective', ObjectivePermissionViewSet, basename='objective')
router.register(r'model', ModelViewSet, basename='model')
router.register(r'model', ModelPermissionViewSet, basename='model')
router.register(r'data_sample', DataSampleViewSet, basename='data_sample')
router.register(r'data_manager', DataManagerViewSet, basename='data_manager')
router.register(r'data_manager', DataManagerPermissionViewSet, basename='data_manager')
router.register(r'algo', AlgoViewSet, basename='algo')
router.register(r'algo', AlgoPermissionViewSet, basename='algo')
router.register(r'traintuple', TrainTupleViewSet, basename='traintuple')
router.register(r'testtuple', TestTupleViewSet, basename='testtuple')
router.register(r'aggregatetuple', AggregateTupleViewSet, basename='aggregatetuple')
router.register(r'task', TaskViewSet, basename='task')
router.register(r'compute_plan', ComputePlanViewSet, basename='compute_plan')
router.register(r'composite_traintuple', CompositeTraintupleViewSet, basename='composite_traintuple')
router.register(r'composite_algo', CompositeAlgoViewSet, basename='composite_algo')
router.register(r'composite_algo', CompositeAlgoPermissionViewSet, basename='composite_algo')
router.register(r'aggregate_algo', AggregateAlgoViewSet, basename='aggregate_algo')
router.register(r'aggregate_algo', AggregateAlgoPermissionViewSet, basename='aggregate_algo')


urlpatterns = [
    url(r'^', include(router.urls)),
]
