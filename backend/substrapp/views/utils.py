import dataclasses
import datetime
import os
import uuid
from typing import Callable
from typing import Optional
from wsgiref.util import is_hop_by_hop

import django.http
from django.conf import settings
from django.db.models import Count
from django.db.models import Q
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings

import orchestrator.common_pb2 as common_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.event_pb2 as event_pb2
import orchestrator.model_pb2 as model_pb2
from localrep.models import ComputeTask as ComputeTaskRep
from localrep.models import DataManager as DataManagerRep
from localrep.models import Metric as MetricRep
from localrep.models import Performance as PerformanceRep
from localrep.serializers import ComputeTaskSerializer as ComputeTaskRepSerializer
from localrep.serializers import DataManagerSerializer as DataManagerRepSerializer
from localrep.serializers import MetricSerializer as MetricRepSerializer
from node.authentication import NodeUser
from orchestrator import failure_report_pb2
from substrapp.clients import node as node_client
from substrapp.compute_tasks import errors
from substrapp.exceptions import AssetPermissionError
from substrapp.exceptions import BadRequestError
from substrapp.orchestrator import get_orchestrator_client
from substrapp.storages.minio import MinioStorage
from substrapp.utils import get_owner

CP_BASENAME_PREFIX = "compute_plan_"

TASK_CATEGORY = {
    "unknown": computetask_pb2.TASK_UNKNOWN,
    "traintuple": computetask_pb2.TASK_TRAIN,
    "testtuple": computetask_pb2.TASK_TEST,
    "aggregatetuple": computetask_pb2.TASK_AGGREGATE,
    "composite_traintuple": computetask_pb2.TASK_COMPOSITE,
}

TASK_FIELD = {
    "traintuple": "train",
    "testtuple": "test",
    "aggregatetuple": "aggregate",
    "composite_traintuple": "composite",
}


MODEL_CATEGORY = {
    "unknown": model_pb2.MODEL_UNKNOWN,
    "simple": model_pb2.MODEL_SIMPLE,
    "head": model_pb2.MODEL_HEAD,
}

HTTP_HEADER_PROXY_ASSET = "Substra-Proxy-Asset"


class ApiResponse(Response):
    """The Content-Disposition header is used for downloads and web service responses
    and indicates to the browser whether the provided file is to be displayed (inline)
    or stored (attachment).
    Some browsers display the file content in the browser if no Content-Disposition header
    is set. Using Content-Disposition: attachment; filename="API-response.json" in production
    is important because it signals the browser not to display the response in the browser.
    """

    def __init__(self, data=None, status=None, template_name=None, headers=None, exception=False, content_type=None):

        if headers is not None:
            if "Content-Disposition" not in headers:
                headers = {**headers, **settings.CONTENT_DISPOSITION_HEADER}
        else:
            headers = settings.CONTENT_DISPOSITION_HEADER

        super().__init__(data, status, template_name, headers, exception, content_type)

    @staticmethod
    def add_content_disposition_header(response):
        response.headers = {**response.headers, **settings.CONTENT_DISPOSITION_HEADER}
        return response


class CustomFileResponse(django.http.FileResponse):
    def set_headers(self, filelike):
        super().set_headers(filelike)

        self["Access-Control-Expose-Headers"] = "Content-Disposition"


def node_has_process_permission(asset):
    """Check if current node can process input asset."""

    if settings.ISOLATED:
        # In isolated frontend there is no access to data
        # (only non sensitive metadata from orchestrator is exported)
        # So by returning always False here, backend will not try to retrieve data
        return False

    permission = asset["permissions"]["process"]
    return permission["public"] or get_owner() in permission["authorized_ids"]


@dataclasses.dataclass
class StorageAddress:
    url: Optional[str]
    node_id: str

    @property
    def is_available(self) -> bool:
        return bool(self.url)

    @property
    def is_local(self) -> bool:
        return get_owner() == self.node_id


class PermissionMixin(object):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES + [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def check_access(self, channel_name: str, user, asset, is_proxied_request: bool) -> None:
        """Returns true if API consumer is allowed to access data.

        :param is_proxied_request: True if the API consumer is another backend-server proxying a user request
        :raises: AssetPermissionError
        """
        if user.is_anonymous:  # safeguard, should never happen
            raise AssetPermissionError()

        permission = self.get_permission(asset)

        if type(user) is NodeUser:  # for node
            node_id = user.username
        else:
            # for classic user, test on current msp id
            node_id = get_owner()

        if not permission["public"] and node_id not in permission["authorized_ids"]:
            raise AssetPermissionError()

    def get_permission(self, asset):
        """Get the permission to check from the asset."""
        # FIXME: This should be 'download' instead of 'process',
        #  but 'download' is not consistently exposed by chaincode yet.
        return asset["permissions"]["process"]

    def get_storage_address(self, asset, orchestrator_field) -> StorageAddress:
        """Returns the storage address of the asset.

        Args:
            asset (Dict): Asset from the Orchestrator
            orchestrator_field (str): Key of the dict containing the storage address

        Returns:
            The asset storage address
        """
        url = asset.get(orchestrator_field, {}).get("storage_address")
        node_id = asset["owner"]
        return StorageAddress(url, node_id)

    def download_file(self, request, query_method, django_field, orchestrator_field=None):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        channel_name = get_channel_name(request)

        validated_key = validate_key(key)

        with get_orchestrator_client(get_channel_name(request)) as client:
            asset = getattr(client, query_method)(validated_key)

        try:
            self.check_access(channel_name, request.user, asset, is_proxied_request(request))
        except AssetPermissionError as e:
            return ApiResponse({"message": str(e)}, status=status.HTTP_403_FORBIDDEN)

        if not orchestrator_field:
            orchestrator_field = django_field
        storage_address = self.get_storage_address(asset, orchestrator_field)
        if not storage_address.is_available:
            return ApiResponse({"message": "Asset not available anymore"}, status=status.HTTP_410_GONE)

        if storage_address.is_local:
            response = self.get_local_file_response(django_field)
        else:
            response = self._download_remote_file(channel_name, storage_address)

        return response

    def download_local_file(self, request, query_method, django_field, orchestrator_field=None):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        validated_key = validate_key(key)

        with get_orchestrator_client(get_channel_name(request)) as client:
            asset = getattr(client, query_method)(validated_key)

        try:
            self.check_access(
                get_channel_name(request),
                request.user,
                asset,
                is_proxied_request(request),
            )
        except AssetPermissionError as e:
            return ApiResponse({"message": str(e)}, status=status.HTTP_403_FORBIDDEN)

        return self.get_local_file_response(django_field)

    def get_local_file_response(self, django_field):
        obj = self.get_object()
        data = getattr(obj, django_field)

        if isinstance(data.storage, MinioStorage):
            filename = str(obj.key)
        else:
            filename = os.path.basename(data.path)
            data = open(data.path, "rb")

        response = CustomFileResponse(
            data,
            as_attachment=True,
            filename=filename,
        )
        return response

    def _download_remote_file(self, channel_name: str, storage_address: StorageAddress) -> django.http.FileResponse:
        proxy_response = node_client.http_get(
            channel=channel_name,
            node_id=storage_address.node_id,
            url=storage_address.url,
            stream=True,
            headers={HTTP_HEADER_PROXY_ASSET: "True"},
        )
        response = CustomFileResponse(
            streaming_content=(chunk for chunk in proxy_response.iter_content(512 * 1024)),
            status=proxy_response.status_code,
        )

        for header in proxy_response.headers:
            # We don't use hop_by_hop headers since they are incompatible
            # with WSGI
            if not is_hop_by_hop(header):
                response[header] = proxy_response.headers.get(header)

        return response


def validate_key(key) -> str:
    """Validates an asset key and return the validated key.

    Args:
        key (str): A valid UUID in string format

    Raises:
        BadRequestError: Raised if the key value isn't an UUID.

    Returns:
        str: A valid UUID in str standard format
    """
    try:
        uid = to_string_uuid(key)
    except ValueError:
        raise BadRequestError(f'key is not a valid UUID: "{key}"')
    return uid


def validate_sort(sort):
    if sort not in ["asc", "desc"]:
        raise BadRequestError(f"Invalid sort value (must be either 'desc' or 'asc'): {sort}")


class ValidationExceptionError(Exception):
    def __init__(self, data, key, st):
        self.data = data
        self.key = key
        self.st = st
        super(ValidationExceptionError).__init__()


def get_channel_name(request):

    if hasattr(request.user, "channel"):
        return request.user.channel.name

    if "Substra-Channel-Name" in request.headers:
        return request.headers["Substra-Channel-Name"]

    raise BadRequestError("Could not determine channel name")


def is_proxied_request(request) -> bool:
    """Return True if the API consumer is another backend-server node proxying a user request.

    :param request: incoming HTTP request
    """
    return HTTP_HEADER_PROXY_ASSET in request.headers


def add_task_extra_information(client, basename, data, channel, expand_relationships=False):
    task_status = computetask_pb2.ComputeTaskStatus.Value(data["status"])

    # add model information on a training compute task or performance on a testing compute task
    if basename in ["traintuple", "aggregatetuple", "composite_traintuple"]:
        if task_status == computetask_pb2.STATUS_DONE:
            data[TASK_FIELD[basename]]["models"] = client.get_computetask_output_models(data["key"])

    # add performances for test tasks
    if basename in ["testtuple"]:
        if task_status == computetask_pb2.STATUS_DONE:
            performances = PerformanceRep.objects.filter(
                compute_task_id=data["key"],
                channel=channel,
            ).order_by("creation_date", "id")
            performances = {str(perf.metric_id): perf.value for perf in performances}
            data[TASK_FIELD[basename]]["perfs"] = performances

    if expand_relationships and basename in ["traintuple", "testtuple", "composite_traintuple"]:
        data_manager = DataManagerRep.objects.get(
            key=data[TASK_FIELD[basename]]["data_manager_key"],
            channel=channel,
        )
        data[TASK_FIELD[basename]]["data_manager"] = DataManagerRepSerializer(data_manager).data

    if expand_relationships and basename == "testtuple":
        metrics = MetricRep.objects.filter(
            key__in=data[TASK_FIELD[basename]]["metric_keys"],
            channel=channel,
        ).order_by("creation_date", "key")
        data[TASK_FIELD[basename]]["metrics"] = MetricRepSerializer(metrics, many=True).data

    if expand_relationships:
        parent_tasks = ComputeTaskRep.objects.filter(
            key__in=data["parent_task_keys"],
            channel=channel,
        ).order_by("creation_date", "key")
        data["parent_tasks"] = ComputeTaskRepSerializer(parent_tasks, many=True).data

    if data["error_type"] is not None:
        data["error_type"] = errors.ComputeTaskErrorType.from_int(
            failure_report_pb2.ErrorType.Value(data["error_type"])
        ).name

    return data


def to_string_uuid(str_or_hex_uuid: uuid.UUID) -> str:
    """converts an UUID string of form 32 char hex string or standard form to a standard form UUID.

    Args:
        str_or_hex_uuid (str): input UUID of form '412511b1-f9f5-49cc-a4bb-4f1640c877f6'
            or '412511b1f9f549cca4bb4f1640c877f6'.

    Returns:
        str: UUID of form '412511b1-f9f5-49cc-a4bb-4f1640c877f6'
    """
    return str(uuid.UUID(str_or_hex_uuid))


def add_cp_task_counts(data):
    stats = ComputeTaskRep.objects.filter(compute_plan__key=data["key"]).aggregate(
        task_count=Count("key"),
        done_count=Count("key", filter=Q(status=computetask_pb2.STATUS_DONE)),
        waiting_count=Count("key", filter=Q(status=computetask_pb2.STATUS_WAITING)),
        todo_count=Count("key", filter=Q(status=computetask_pb2.STATUS_TODO)),
        doing_count=Count("key", filter=Q(status=computetask_pb2.STATUS_DOING)),
        canceled_count=Count("key", filter=Q(status=computetask_pb2.STATUS_CANCELED)),
        failed_count=Count("key", filter=Q(status=computetask_pb2.STATUS_FAILED)),
    )
    data.update(stats)
    return data


def add_compute_plan_duration_or_eta(client, data):
    """Add the duration and the estimated time of arrival or end date to a compute plan data."""

    current_date = datetime.datetime.now()
    compute_plan_status = computeplan_pb2.ComputePlanStatus.Value(data["status"])

    start_date = None
    end_date = None
    data["start_date"] = None
    data["end_date"] = None
    data["estimated_end_date"] = None
    data["duration"] = None

    first_event = next(
        client.query_events_generator(
            event_kind=event_pb2.EVENT_ASSET_UPDATED,
            metadata={"status": "STATUS_DOING", "compute_plan_key": data["key"]},
        ),
        None,
    )

    last_event = next(
        client.query_events_generator(
            event_kind=event_pb2.EVENT_ASSET_UPDATED,
            metadata={"compute_plan_key": data["key"]},
            sort=common_pb2.DESCENDING,
        ),
        None,
    )

    if (
        compute_plan_status
        in [
            computeplan_pb2.PLAN_STATUS_DOING,
            computeplan_pb2.PLAN_STATUS_FAILED,
            computeplan_pb2.PLAN_STATUS_CANCELED,
            computeplan_pb2.PLAN_STATUS_DONE,
        ]
        and first_event
    ):
        data["start_date"] = first_event["timestamp"]
        if data["start_date"]:
            start_date = datetime.datetime.strptime(
                first_event["timestamp"].split("+")[0].strip("Z")[:-3], "%Y-%m-%dT%H:%M:%S.%f"
            )

    # duration and estimated_end_date
    if compute_plan_status == computeplan_pb2.PLAN_STATUS_DOING:
        if data["done_count"] and start_date is not None:
            remaining_tasks_count = data["task_count"] - data["done_count"]
            current_duration = current_date - start_date
            time_per_task = current_duration / data["done_count"]
            estimated_duration = remaining_tasks_count * time_per_task
            data["duration"] = int(current_duration.total_seconds())
            data["estimated_end_date"] = (current_date + estimated_duration).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    if (
        compute_plan_status
        in [computeplan_pb2.PLAN_STATUS_FAILED, computeplan_pb2.PLAN_STATUS_CANCELED, computeplan_pb2.PLAN_STATUS_DONE]
        and last_event
    ):

        data["end_date"] = last_event["timestamp"]
        data["estimated_end_date"] = data["end_date"]
        if data["end_date"]:
            end_date = datetime.datetime.strptime(
                last_event["timestamp"].split("+")[0].strip("Z")[:-3], "%Y-%m-%dT%H:%M:%S.%f"
            )

        if start_date is not None and end_date is not None:
            data["duration"] = int((end_date - start_date).total_seconds())

    return data


def if_true(decorator: Callable, condition: bool):
    """Decorates a function only if the condition is true

    Args:
        decorator (Callable): The decorator function to apply
        condition (bool): If true the decorator is applied, else we just run the decorated function
    """

    def wrapper(func):
        if not condition:
            return func
        return decorator(func)

    return wrapper
