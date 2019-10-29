"""
substrapp URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from substrapp.views import ObjectiveViewSet, DataSampleViewSet, DataManagerViewSet, \
    AlgoViewSet, TrainTupleViewSet, TestTupleViewSet, ModelViewSet, TaskViewSet, \
    ComputePlanViewSet, ObjectivePermissionViewSet, AlgoPermissionViewSet, DataManagerPermissionViewSet, \
    ModelPermissionViewSet, CompositeTupleViewSet, CompositeAlgoViewSet


# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r'objective', ObjectiveViewSet, base_name='objective')
router.register(r'objective', ObjectivePermissionViewSet, base_name='objective')
router.register(r'model', ModelViewSet, base_name='model')
router.register(r'model', ModelPermissionViewSet, base_name='model')
router.register(r'data_sample', DataSampleViewSet, base_name='data_sample')
router.register(r'data_manager', DataManagerViewSet, base_name='data_manager')
router.register(r'data_manager', DataManagerPermissionViewSet, base_name='data_manager')
router.register(r'algo', AlgoViewSet, base_name='algo')
router.register(r'algo', AlgoPermissionViewSet, base_name='algo')
router.register(r'traintuple', TrainTupleViewSet, base_name='traintuple')
router.register(r'testtuple', TestTupleViewSet, base_name='testtuple')
router.register(r'task', TaskViewSet, base_name='task')
router.register(r'compute_plan', ComputePlanViewSet, base_name='compute_plan')
router.register(r'compositetuple', CompositeTupleViewSet, base_name='compositetuple')
router.register(r'compositealgo', CompositeAlgoViewSet, base_name='compositealgo')

urlpatterns = [
    url(r'^', include(router.urls)),
]
