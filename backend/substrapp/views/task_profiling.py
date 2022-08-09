from typing import Any

import structlog
from django.db.models.query import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

from libs.pagination import LargePageNumberPagination
from localrep.models import TaskProfiling
from localrep.serializers import TaskProfilingSerializer
from localrep.serializers.task_profiling import ProfilingStepSerializer
from substrapp.views.utils import IsCurrentBackendOrReadOnly
from substrapp.views.utils import get_channel_name

logger = structlog.get_logger(__name__)


class TaskProfilingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    filter_backends = (DjangoFilterBackend,)
    serializer_class = TaskProfilingSerializer
    pagination_class = LargePageNumberPagination
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES + [BasicAuthentication]
    permission_classes = [IsAuthenticated, IsCurrentBackendOrReadOnly]

    def get_queryset(self) -> QuerySet[TaskProfiling]:
        return TaskProfiling.objects.filter(compute_task__channel=get_channel_name(self.request))


class TaskProfilingStepViewSet(mixins.CreateModelMixin, GenericViewSet):
    serializer_class = ProfilingStepSerializer
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES + [BasicAuthentication]
    permission_classes = [IsAuthenticated, IsCurrentBackendOrReadOnly]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        task_profile_pk = kwargs["task_profiling_pk"]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(compute_task_profile_id=task_profile_pk)
        return Response(serializer.data)
