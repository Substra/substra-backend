from typing import Any

import structlog
from django.db.models.query import QuerySet
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

from api.models import ProfilingStep
from api.models import TaskProfiling
from api.serializers import TaskProfilingSerializer
from api.serializers.task_profiling import ProfilingStepSerializer
from api.views.utils import IsCurrentBackendOrReadOnly
from api.views.utils import get_channel_name
from libs.pagination import LargePageNumberPagination
from libs.permissions import IsAuthorized

logger = structlog.get_logger(__name__)


class TaskProfilingViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    filter_backends = (DjangoFilterBackend,)
    serializer_class = TaskProfilingSerializer
    pagination_class = LargePageNumberPagination
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES + [BasicAuthentication]
    permission_classes = [IsAuthorized, IsCurrentBackendOrReadOnly]

    def get_queryset(self) -> QuerySet[TaskProfiling]:
        return TaskProfiling.objects.filter(compute_task__channel=get_channel_name(self.request))

    def create(self, request: Request, *args: Any, **kwargs: Any):
        try:
            task_profiling = super().create(request, *args, **kwargs)
        except IntegrityError:
            data = {"detail": f"TaskProfiling with key {request.data['compute_task_key']} already exists"}
            return Response(data, status=status.HTTP_409_CONFLICT)
        return task_profiling

    def perform_update(self, serializer):
        kwargs = {"creation_date": timezone.now()}
        return serializer.save(**kwargs)


class TaskProfilingStepViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    serializer_class = ProfilingStepSerializer
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES + [BasicAuthentication]
    permission_classes = [IsAuthorized, IsCurrentBackendOrReadOnly]
    lookup_field = "step"

    def get_queryset(self) -> QuerySet[TaskProfiling]:
        return ProfilingStep.objects.filter(compute_task_profile__compute_task__channel=get_channel_name(self.request))

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        task_profile_pk = kwargs["task_profiling_pk"]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save(compute_task_profile_id=task_profile_pk)
        except IntegrityError:
            data = {"detail": f"Profiling with key {task_profile_pk} and name {request.data['step']} already exists"}
            return Response(data, status=status.HTTP_409_CONFLICT)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_object(self):
        queryset = self.get_queryset()
        filters = {**self.kwargs}
        filters["compute_task_profile_id"] = filters.pop("task_profiling_pk")
        obj = get_object_or_404(queryset, **filters)

        self.check_object_permissions(self.request, obj)
        return obj
