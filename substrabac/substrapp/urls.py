"""
substrapp URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from substrapp.views import ObjectiveViewSet, DataSampleViewSet, DataManagerViewSet, \
    AlgoViewSet, TrainTupleViewSet, TestTupleViewSet, ModelViewSet, TaskViewSet, \
<<<<<<< HEAD
    ComputePlanViewSet, ObjectivePermissionViewSet, AlgoPermissionViewSet, DataManagerPermissionViewSet, \
<<<<<<< HEAD
    ModelPermissionViewSet, NodeViewSet, PermissionNodeViewSet
=======
    NodeViewSet
>>>>>>> add current node view
=======
    ComputePlanViewSet, ObjectivePermissionViewSet, AlgoPermissionViewSet, DataManagerPermissionViewSet
>>>>>>> Place node view in its own app

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
<<<<<<< HEAD
router.register(r'node', NodeViewSet, base_name='node')
<<<<<<< HEAD
router.register(r'permission_node', PermissionNodeViewSet, base_name='permission_node')
=======
>>>>>>> add current node view
=======
>>>>>>> Place node view in its own app

urlpatterns = [
    url(r'^', include(router.urls)),
]
