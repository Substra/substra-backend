"""
substrapp URL
"""

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

import substrapp.views as views
from substrapp.views.computeplan import BASENAME_PREFIX

# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r'metric', views.MetricViewSet, basename='metric')
router.register(r'metric', views.MetricPermissionViewSet, basename='metric')
router.register(r'model', views.ModelViewSet, basename='model')
router.register(r'model', views.ModelPermissionViewSet, basename='model')
router.register(r'data_sample', views.DataSampleViewSet, basename='data_sample')
router.register(r'data_manager', views.DataManagerViewSet, basename='data_manager')
router.register(r'data_manager', views.DataManagerPermissionViewSet, basename='data_manager')
router.register(r'algo', views.AlgoViewSet, basename='algo')
router.register(r'algo', views.AlgoPermissionViewSet, basename='algo')
router.register(r'traintuple', views.ComputeTaskViewSet, basename='traintuple')
router.register(r'testtuple', views.ComputeTaskViewSet, basename='testtuple')
router.register(r'aggregatetuple', views.ComputeTaskViewSet, basename='aggregatetuple')
router.register(r'composite_traintuple', views.ComputeTaskViewSet, basename='composite_traintuple')
router.register(r'compute_plan', views.ComputePlanViewSet, basename='compute_plan')

compute_plan_router = routers.NestedDefaultRouter(router, r"compute_plan", lookup="compute_plan")
compute_plan_router.register(r"traintuple", views.CPTaskViewSet, basename=f'{BASENAME_PREFIX}traintuple')
compute_plan_router.register(r"aggregatetuple", views.CPTaskViewSet, basename=f'{BASENAME_PREFIX}aggregatetuple')
compute_plan_router.register(r"composite_traintuple", views.CPTaskViewSet,
                             basename=f'{BASENAME_PREFIX}composite_traintuple')
compute_plan_router.register(r"testtuple", views.CPTaskViewSet, basename=f'{BASENAME_PREFIX}testtuple')
compute_plan_router.register(r"algos", views.CPAlgoViewSet, basename=f'{BASENAME_PREFIX}algo')


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(compute_plan_router.urls)),
]
