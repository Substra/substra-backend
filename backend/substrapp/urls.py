"""
substrapp URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

import substrapp.views as views


# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r'objective', views.ObjectiveViewSet, basename='objective')
router.register(r'objective', views.ObjectivePermissionViewSet, basename='objective')
router.register(r'model', views.ModelViewSet, basename='model')
router.register(r'model', views.ModelPermissionViewSet, basename='model')
router.register(r'data_sample', views.DataSampleViewSet, basename='data_sample')
router.register(r'data_manager', views.DataManagerViewSet, basename='data_manager')
router.register(r'data_manager', views.DataManagerPermissionViewSet, basename='data_manager')
router.register(r'algo', views.AlgoViewSet, basename='algo')
router.register(r'algo', views.AlgoPermissionViewSet, basename='algo')
router.register(r'traintuple', views.TrainTupleViewSet, basename='traintuple')
router.register(r'testtuple', views.TestTupleViewSet, basename='testtuple')
router.register(r'aggregatetuple', views.AggregateTupleViewSet, basename='aggregatetuple')
router.register(r'compute_plan', views.ComputePlanViewSet, basename='compute_plan')
router.register(r'composite_traintuple', views.CompositeTraintupleViewSet, basename='composite_traintuple')
router.register(r'composite_algo', views.CompositeAlgoViewSet, basename='composite_algo')
router.register(r'composite_algo', views.CompositeAlgoPermissionViewSet, basename='composite_algo')
router.register(r'aggregate_algo', views.AggregateAlgoViewSet, basename='aggregate_algo')
router.register(r'aggregate_algo', views.AggregateAlgoPermissionViewSet, basename='aggregate_algo')

compute_plan_router = routers.NestedDefaultRouter(router, r"compute_plan", lookup="compute_plan")
compute_plan_router.register(r"traintuple", views.CPTraintupleViewSet, basename="compute_plan_traintuple")
compute_plan_router.register(r"aggregatetuple", views.CPAggregatetupleViewSet, basename="compute_plan_aggregatetuple")
compute_plan_router.register(r"composite_traintuple", views.CPCompositeTraintupleViewSet,
                             basename="compute_plan_composite_traintuple")
compute_plan_router.register(r"testtuple", views.CPTesttupleViewSet, basename="compute_plan_testtuple")


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(compute_plan_router.urls)),
]
