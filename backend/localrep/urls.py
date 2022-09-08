"""
localrep URL
"""

from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

import localrep.views as views
from localrep.views.utils import CP_BASENAME_PREFIX

# Create a router and register our viewsets with it.

router = DefaultRouter()
router.register(r"model", views.ModelViewSet, basename="model")
router.register(r"model", views.ModelPermissionViewSet, basename="model")
router.register(r"data_sample", views.DataSampleViewSet, basename="data_sample")
router.register(r"data_manager", views.DataManagerViewSet, basename="data_manager")
router.register(r"data_manager", views.DataManagerPermissionViewSet, basename="data_manager")
router.register(r"algo", views.AlgoViewSet, basename="algo")
router.register(r"algo", views.AlgoPermissionViewSet, basename="algo")
router.register(r"traintuple", views.ComputeTaskViewSet, basename="traintuple")
router.register(r"predicttuple", views.ComputeTaskViewSet, basename="predicttuple")
router.register(r"testtuple", views.ComputeTaskViewSet, basename="testtuple")
router.register(r"aggregatetuple", views.ComputeTaskViewSet, basename="aggregatetuple")
router.register(r"composite_traintuple", views.ComputeTaskViewSet, basename="composite_traintuple")
router.register(r"compute_plan", views.ComputePlanViewSet, basename="compute_plan")
router.register(r"compute_plan_metadata", views.ComputePlanMetadataViewSet, basename="compute_plan_metadata")
router.register(r"news_feed", views.NewsFeedViewSet, basename="news_feed")
router.register(r"performance", views.PerformanceViewSet, basename="performance")
router.register(r"logs", views.ComputeTaskLogsViewSet, basename="logs")
router.register(r"task_profiling", views.TaskProfilingViewSet, basename="task_profiling")

task_profiling_router = routers.NestedDefaultRouter(router, r"task_profiling", lookup="task_profiling")
task_profiling_router.register(r"step", views.TaskProfilingStepViewSet, basename="step")

compute_plan_router = routers.NestedDefaultRouter(router, r"compute_plan", lookup="compute_plan")
compute_plan_router.register(r"traintuple", views.CPTaskViewSet, basename=f"{CP_BASENAME_PREFIX}traintuple")
compute_plan_router.register(r"aggregatetuple", views.CPTaskViewSet, basename=f"{CP_BASENAME_PREFIX}aggregatetuple")
compute_plan_router.register(
    r"composite_traintuple", views.CPTaskViewSet, basename=f"{CP_BASENAME_PREFIX}composite_traintuple"
)
compute_plan_router.register(r"predicttuple", views.CPTaskViewSet, basename=f"{CP_BASENAME_PREFIX}predicttuple")
compute_plan_router.register(r"testtuple", views.CPTaskViewSet, basename=f"{CP_BASENAME_PREFIX}testtuple")
compute_plan_router.register(r"algos", views.CPAlgoViewSet, basename=f"{CP_BASENAME_PREFIX}algo")
compute_plan_router.register(r"perf", views.CPPerformanceViewSet, basename=f"{CP_BASENAME_PREFIX}perf")


urlpatterns = [
    path("", include(router.urls)),
    path("", include(compute_plan_router.urls)),
    path("", include(task_profiling_router.urls)),
    path(r"task/bulk_create/", views.task_bulk_create_view, name="task_bulk_create"),
    path(r"compute_plan/<compute_plan_pk>/workflow_graph/", views.get_cp_graph, name="workflow_graph"),
]
