import structlog
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

import orchestrator.algo_pb2 as algo_pb2
from libs.pagination import DefaultPageNumberPagination
from localrep.errors import AlreadyExistsError
from localrep.models import Algo as AlgoRep
from localrep.serializers import AlgoSerializer as AlgoRepSerializer
from substrapp.models import Algo
from substrapp.serializers import AlgoSerializer
from substrapp.serializers import OrchestratorAlgoSerializer
from substrapp.utils import get_hash
from substrapp.views.filters_utils import CustomSearchFilter
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import PermissionMixin
from substrapp.views.utils import ValidationExceptionError
from substrapp.views.utils import get_channel_name
from substrapp.views.utils import validate_key

logger = structlog.get_logger(__name__)


def _register_in_orchestrator(request, instance):
    """Register algo in orchestrator."""
    try:
        category = algo_pb2.AlgoCategory.Value(request.data.get("category"))
    except ValueError:
        raise ValidationError({"category": "Invalid category"})

    orchestrator_serializer = OrchestratorAlgoSerializer(
        data={
            "name": request.data.get("name"),
            "category": category,
            "permissions": request.data.get("permissions"),
            "metadata": request.data.get("metadata"),
            "instance": instance,
        },
        context={"request": request},
    )
    orchestrator_serializer.is_valid(raise_exception=True)
    return orchestrator_serializer.create(get_channel_name(request), orchestrator_serializer.validated_data)


def create(request, get_success_headers):
    """Create a new algo.

    The workflow is composed of several steps:
    - Save files in local database to get the addresses.
    - Register asset in the orchestrator.
    - Save metadata in local database.
    """
    # Step1: save files in local database
    file = request.data.get("file")
    try:
        checksum = get_hash(file)
    except Exception as e:
        raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

    serializer = AlgoSerializer(
        data={"file": file, "description": request.data.get("description"), "checksum": checksum}
    )

    try:
        serializer.is_valid(raise_exception=True)
    except Exception as e:
        raise ValidationExceptionError(e.args, "(not computed)", status.HTTP_400_BAD_REQUEST)

    instance = serializer.save()

    # Step2: register asset in orchestrator
    try:
        localrep_data = _register_in_orchestrator(request, instance)
    except Exception:
        instance.delete()  # warning: post delete signals are not executed by django rollback
        raise

    # Step3: save metadata in local database
    localrep_data["channel"] = get_channel_name(request)
    localrep_serializer = AlgoRepSerializer(data=localrep_data)
    try:
        localrep_serializer.save_if_not_exists()
    except AlreadyExistsError:
        # May happen if the events app already processed the event pushed by the orchestrator
        algo = AlgoRep.objects.get(key=localrep_data["key"])
        data = AlgoRepSerializer(algo).data
    except Exception:
        instance.delete()  # warning: post delete signals are not executed by django rollback
        raise
    else:
        data = localrep_serializer.data

    # Returns algo metadata from local database (and algo data) to ensure consistency between GET and CREATE views
    data.update(serializer.data)

    # Return ApiResponse
    headers = get_success_headers(data)
    return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)


def map_category(key, values):
    if key == "category":
        values = [algo_pb2.AlgoCategory.Value(value) for value in values]
    return key, values


class AlgoViewSetConfig:
    serializer_class = AlgoRepSerializer
    filter_backends = (OrderingFilter, CustomSearchFilter)
    ordering_fields = ["creation_date", "key", "name", "owner", "category"]
    ordering = ["creation_date", "key"]
    pagination_class = DefaultPageNumberPagination
    custom_search_object_type = "algo"
    custom_search_mapping_callback = map_category

    def get_queryset(self):
        return AlgoRep.objects.filter(channel=get_channel_name(self.request))


class AlgoViewSet(
    AlgoViewSetConfig, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet
):
    def create(self, request, *args, **kwargs):
        return create(request, lambda data: self.get_success_headers(data))


class CPAlgoViewSet(AlgoViewSetConfig, mixins.ListModelMixin, GenericViewSet):
    def get_queryset(self):
        compute_plan_key = self.kwargs.get("compute_plan_pk")
        validate_key(compute_plan_key)
        queryset = super().get_queryset()
        return queryset.filter(compute_tasks__compute_plan__key=compute_plan_key).distinct()


class AlgoPermissionViewSet(PermissionMixin, GenericViewSet):
    queryset = Algo.objects.all()
    serializer_class = AlgoSerializer

    @action(detail=True)
    def file(self, request, *args, **kwargs):
        return self.download_file(request, AlgoRep, "file", "algorithm_address")

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions
    @action(detail=True, url_path="description", url_name="description")
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, AlgoRep, "description", "description_address")
