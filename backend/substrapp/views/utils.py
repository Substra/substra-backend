import os
import uuid
import datetime

from django.conf import settings
from django.http import FileResponse
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings

from node.authentication import NodeUser
from substrapp.utils import get_remote_file, get_owner, get_remote_file_content
from node.models import OutgoingNode
from substrapp.storages.minio import MinioStorage


from rest_framework import status
from requests.auth import HTTPBasicAuth
from wsgiref.util import is_hop_by_hop

from substrapp.exceptions import AssetPermissionError, NodeError, BadRequestError
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.event_pb2 as event_pb2
import orchestrator.common_pb2 as common_pb2
import orchestrator.model_pb2 as model_pb2
from orchestrator.error import OrcError
from substrapp.orchestrator import get_orchestrator_client


TASK_CATEGORY = {
    'unknown': computetask_pb2.TASK_UNKNOWN,
    'traintuple': computetask_pb2.TASK_TRAIN,
    'testtuple': computetask_pb2.TASK_TEST,
    'aggregatetuple': computetask_pb2.TASK_AGGREGATE,
    'composite_traintuple': computetask_pb2.TASK_COMPOSITE
}

TASK_FIELD = {
    'traintuple': 'train',
    'testtuple': 'test',
    'aggregatetuple': 'aggregate',
    'composite_traintuple': 'composite'
}


MODEL_CATEGORY = {
    'unknown': model_pb2.MODEL_UNKNOWN,
    'simple': model_pb2.MODEL_SIMPLE,
    'head': model_pb2.MODEL_HEAD,
}


HTTP_HEADER_PROXY_ASSET = "Substra-Proxy-Asset"


def authenticate_outgoing_request(outgoing_node_id):
    try:
        outgoing = OutgoingNode.objects.get(node_id=outgoing_node_id)
    except OutgoingNode.DoesNotExist:
        raise NodeError(
            f"Unauthorized to call remote node with node_id: {outgoing_node_id}"
        )

    # to authenticate to remote node we use the current node id
    # with the associated outgoing secret.
    current_node_id = get_owner()

    return HTTPBasicAuth(current_node_id, outgoing.secret)


def get_remote_asset(channel_name, url, node_id, content_checksum, salt=None):
    auth = authenticate_outgoing_request(node_id)
    return get_remote_file_content(channel_name, url, auth, content_checksum, salt=salt)


class CustomFileResponse(FileResponse):
    def set_headers(self, filelike):
        super(CustomFileResponse, self).set_headers(filelike)

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


class PermissionMixin(object):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES + [
        BasicAuthentication
    ]
    permission_classes = [IsAuthenticated]

    def check_access(
        self, channel_name: str, user, asset, is_proxied_request: bool
    ) -> None:
        """Returns true if API consumer is allowed to access data.

        :param is_proxied_request: True if the API consumer is another backend-server proxying a user request
        :raises: AssetPermissionError
        """
        if user.is_anonymous:  # safeguard, should never happened
            raise AssetPermissionError()

        if type(user) is NodeUser:  # for node
            permission = asset["permissions"]["process"]
            node_id = user.username
        else:
            # for classic user, test on current msp id
            # TODO: This should be 'download' instead of 'process',
            #       but 'download' is not consistently exposed by chaincode yet.
            permission = asset["permissions"]["process"]
            node_id = get_owner()

        if not permission["public"] and node_id not in permission["authorized_ids"]:
            raise AssetPermissionError()

    def get_storage_address(self, asset, ledger_field) -> str:
        """returns the storage address of the asset or nothing if there is no storage address

        Args:
            asset (Dict): Asset from the Orchestrator
            ledger_field (str): Key of the dict containing the storage address

        Returns:
            str: The asset storage address
        """
        return asset.get(ledger_field, {}).get("storage_address")

    def download_file(
        self, request, query_method, django_field, orchestrator_field=None
    ):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        channel_name = get_channel_name(request)

        validated_key = validate_key(key)

        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                asset = getattr(client, query_method)(validated_key)
        except OrcError as rpc_error:
            return Response(
                {"message": rpc_error.details}, status=rpc_error.http_status()
            )

        try:
            self.check_access(
                channel_name, request.user, asset, is_proxied_request(request)
            )
        except AssetPermissionError as e:
            return Response({"message": str(e)}, status=status.HTTP_403_FORBIDDEN)

        if not orchestrator_field:
            orchestrator_field = django_field
        storage_address = self.get_storage_address(asset, orchestrator_field)
        if not storage_address:
            return Response({"message": "Asset not available anymore"}, status=status.HTTP_410_GONE)

        if get_owner() == asset["owner"]:
            response = self.get_local_file_response(django_field)
        else:
            response = self._download_remote_file(channel_name, storage_address, asset)

        return response

    def download_local_file(
        self, request, query_method, django_field, orchestrator_field=None
    ):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        validated_key = validate_key(key)

        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                asset = getattr(client, query_method)(validated_key)
        except OrcError as rpc_error:
            return Response(
                {"message": rpc_error.details}, status=rpc_error.http_status()
            )

        try:
            self.check_access(
                get_channel_name(request),
                request.user,
                asset,
                is_proxied_request(request),
            )
        except AssetPermissionError as e:
            return Response({"message": str(e)}, status=status.HTTP_403_FORBIDDEN)

        if not orchestrator_field:
            orchestrator_field = django_field

        return self.get_local_file_response(django_field)

    def get_local_file_response(self, django_field):
        obj = self.get_object()
        data = getattr(obj, django_field)
        filename = None

        if hasattr(obj, 'file') and isinstance(obj.file.storage, MinioStorage):
            filename = str(obj.key)
        else:
            filename = os.path.basename(data.path)
            data = open(data.path, 'rb')

        response = CustomFileResponse(
            data,
            as_attachment=True,
            filename=filename,
        )
        return response

    def _download_remote_file(self, channel_name, storage_address, asset):
        node_id = asset["owner"]
        auth = authenticate_outgoing_request(node_id)

        r = get_remote_file(
            channel_name,
            storage_address,
            auth,
            stream=True,
            headers={HTTP_HEADER_PROXY_ASSET: "True"},
        )

        if not r.ok:
            return Response(
                {
                    "message": f'Cannot proxify asset from node {asset["owner"]}: {str(r.text)}'
                },
                status=r.status_code,
            )

        response = CustomFileResponse(
            streaming_content=(chunk for chunk in r.iter_content(512 * 1024)),
            status=r.status_code,
        )

        for header in r.headers:
            # We don't use hop_by_hop headers since they are incompatible
            # with WSGI
            if not is_hop_by_hop(header):
                response[header] = r.headers.get(header)

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
        raise BadRequestError(
            f"Invalid sort value (must be either 'desc' or 'asc'): {sort}"
        )


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


def add_task_extra_information(client, basename, data, expand_relationships=False):

    task_status = computetask_pb2.ComputeTaskStatus.Value(data['status'])

    # add model information on a training compute task or performance on a testing compute task
    if basename in ['traintuple', 'aggregatetuple', 'composite_traintuple']:
        if task_status == computetask_pb2.STATUS_DONE:
            data[TASK_FIELD[basename]]['models'] = client.get_computetask_output_models(data['key'])

    # add performances for test tasks
    if basename in ['testtuple']:
        if task_status == computetask_pb2.STATUS_DONE:
            performances = client.get_compute_task_performances(data['key'])
            performances = {performance['metric_key']: performance['performance_value']
                            for performance in performances}
            data[TASK_FIELD[basename]]['perfs'] = performances

    if expand_relationships and basename in ['traintuple', 'testtuple', 'composite_traintuple']:
        data_manager_key = data[TASK_FIELD[basename]]['data_manager_key']
        data[TASK_FIELD[basename]]['data_manager'] = client.query_datamanager(data_manager_key)

    if expand_relationships and basename == 'testtuple':
        metric_keys = data[TASK_FIELD[basename]]['metric_keys']
        data[TASK_FIELD[basename]]['metrics'] = [client.query_metric(metric_key) for metric_key in metric_keys]

    if expand_relationships:
        data['parent_tasks'] = [client.query_task(key) for key in data['parent_task_keys']]

    # fetch task start and end dates from its events
    first_event = next(
        client.query_events_generator(
            event_kind=event_pb2.EVENT_ASSET_UPDATED,
            asset_key=data['key'],
            metadata={'status': 'STATUS_DOING'}
        ),
        None
    )
    data['start_date'] = first_event['timestamp'] if first_event else None

    if task_status in [computetask_pb2.STATUS_FAILED,
                       computetask_pb2.STATUS_CANCELED,
                       computetask_pb2.STATUS_DONE]:
        last_event = next(
            client.query_events_generator(
                event_kind=event_pb2.EVENT_ASSET_UPDATED,
                asset_key=data['key'],
                sort=common_pb2.DESCENDING
            ),
            None
        )
    else:
        last_event = None
    data['end_date'] = last_event['timestamp'] if last_event else None

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


def add_cp_extra_information(client, data):
    data = add_compute_plan_failed_task(client, data)
    data = add_compute_plan_duration_or_eta(client, data)

    return data


def add_compute_plan_failed_task(client, data):
    """Add the first failed task information to a compute plan data.
    It helps the final user to find which task failed the compute plan.
    """

    if computeplan_pb2.ComputePlanStatus.Value(data["status"]) == computeplan_pb2.PLAN_STATUS_FAILED:

        first_failed_task = next(
            client.query_events_generator(
                event_kind=event_pb2.EVENT_ASSET_UPDATED,
                metadata={"status": "STATUS_FAILED", "compute_plan_key": data["key"]}
            ),
            None
        )

        failed_task = client.query_task(key=first_failed_task["asset_key"])

        data["failed_task"] = {}
        data["failed_task"]["key"] = failed_task["key"]
        data["failed_task"]["category"] = failed_task["category"]
    else:
        data["failed_task"] = None

    return data


def add_compute_plan_duration_or_eta(client, data):
    """Add the duration and the estimated time of arrival or end date to a compute plan data.
    """

    current_date = datetime.datetime.now()
    compute_plan_status = computeplan_pb2.ComputePlanStatus.Value(data["status"])

    start_date = None
    data["start_date"] = None
    end_date = None
    data["end_date"] = None
    data["estimated_end_date"] = None
    data["duration"] = None

    first_event = next(
        client.query_events_generator(
            event_kind=event_pb2.EVENT_ASSET_UPDATED,
            metadata={"status": "STATUS_DOING", "compute_plan_key": data["key"]}
        ),
        None
    )

    last_event = next(
        client.query_events_generator(
            event_kind=event_pb2.EVENT_ASSET_UPDATED,
            metadata={"compute_plan_key": data["key"]},
            sort=common_pb2.DESCENDING
        ),
        None
    )

    if compute_plan_status in [computeplan_pb2.PLAN_STATUS_DOING,
                               computeplan_pb2.PLAN_STATUS_FAILED,
                               computeplan_pb2.PLAN_STATUS_CANCELED,
                               computeplan_pb2.PLAN_STATUS_DONE] and first_event:
        data["start_date"] = first_event["timestamp"]
        if data["start_date"]:
            start_date = datetime.datetime.strptime(first_event["timestamp"].split('+')[0].strip("Z")[:-3],
                                                    "%Y-%m-%dT%H:%M:%S.%f")

    # duration and estimated_end_date
    if compute_plan_status == computeplan_pb2.PLAN_STATUS_DOING:
        if data["done_count"] and start_date is not None:
            remaining_tasks_count = data["task_count"] - data["done_count"]
            current_duration = current_date - start_date
            time_per_task = current_duration / data["done_count"]
            estimated_duration = remaining_tasks_count * time_per_task
            data["duration"] = int(current_duration.total_seconds())
            data["estimated_end_date"] = (current_date + estimated_duration).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    if compute_plan_status in [computeplan_pb2.PLAN_STATUS_FAILED,
                               computeplan_pb2.PLAN_STATUS_CANCELED,
                               computeplan_pb2.PLAN_STATUS_DONE] and last_event:

        data["end_date"] = last_event["timestamp"]
        data["estimated_end_date"] = data["end_date"]
        if data["end_date"]:
            end_date = datetime.datetime.strptime(last_event["timestamp"].split('+')[0].strip("Z")[:-3],
                                                  "%Y-%m-%dT%H:%M:%S.%f")
            data["duration"] = int((end_date - start_date).total_seconds())

    return data
