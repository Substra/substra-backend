import structlog
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

from libs.pagination import DefaultPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import Metric as MetricRep
from localrep.serializers import MetricSerializer as MetricRepSerializer
from substrapp.models import Metric
from substrapp.serializers import MetricSerializer
from substrapp.serializers import OrchestratorMetricSerializer
from substrapp.utils import get_hash
from substrapp.views.filters_utils import CustomSearchFilter
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import PermissionMixin
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import get_channel_name

logger = structlog.get_logger(__name__)


def create(request, get_success_headers):
    """Create a new metric.

    The workflow is composed of several steps:
    - Save files in local database to get the addresses.
        This is needed as we need the addresses.
    - Register asset in the orchestrator.
    - Save metadata in local database.
    """
    # Step1: save files in local database
    description = request.data.get("description")
    try:
        checksum = get_hash(description)
    except Exception as e:
        raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

    serializer = MetricSerializer(
        data={"address": request.data.get("file"), "description": description, "checksum": checksum}
    )

    try:
        serializer.is_valid(raise_exception=True)
    except Exception as e:
        raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

    instance = serializer.save()

    # Step2: register asset in orchestrator
    try:
        orchestrator_serializer = OrchestratorMetricSerializer(
            data={
                "name": request.data.get("name"),
                "permissions": request.data.get("permissions"),
                "metadata": request.data.get("metadata"),
                "instance": instance,
            },
            context={"request": request},
        )
        orchestrator_serializer.is_valid(raise_exception=True)
        localrep_data = orchestrator_serializer.create(
            get_channel_name(request), orchestrator_serializer.validated_data
        )
    except Exception:
        instance.delete()  # warning: post delete signals are not executed by django rollback
        raise

    # Step3: save metadata in local database
    localrep_data["channel"] = get_channel_name(request)
    localrep_serializer = MetricRepSerializer(data=localrep_data)
    try:
        localrep_serializer.save_if_not_exists()
    except AlreadyExistsError:
        # May happen if the events app already processed the event pushed by the orchestrator
        metric = MetricRep.objects.get(key=localrep_data["key"])
        data = MetricRepSerializer(metric).data
    except Exception:
        instance.delete()  # warning: post delete signals are not executed by django rollback
        raise
    else:
        data = localrep_serializer.data

    # Use metric metadata from local database to ensure consistency between GET and CREATE views
    data.update(serializer.data)

    # Return ApiResponse
    headers = get_success_headers(data)
    return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)


class MetricViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = MetricRepSerializer
    filter_backends = (OrderingFilter, CustomSearchFilter)
    ordering_fields = ["creation_date", "key", "name", "owner"]
    ordering = ["creation_date", "key"]
    pagination_class = DefaultPageNumberPagination
    custom_search_object_type = "metric"

    def get_queryset(self):
        return MetricRep.objects.filter(channel=get_channel_name(self.request))

    def create(self, request, *args, **kwargs):
        return create(request, lambda data: self.get_success_headers(data))


class MetricPermissionViewSet(PermissionMixin, GenericViewSet):
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions
    @action(detail=True, url_path="description", url_name="description")
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, MetricRep, "description", "description_address")

    @action(detail=True)
    def metrics(self, request, *args, **kwargs):
        return self.download_file(request, MetricRep, "address", "metric_address")
