import datetime
import time
from copy import deepcopy
from functools import wraps
from typing import Generator

import grpc
import structlog
from django.conf import settings
from django.utils.duration import duration_microseconds
from google.protobuf.json_format import MessageToDict

import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.datamanager_pb2 as datamanager_pb2
import orchestrator.datasample_pb2 as datasample_pb2
import orchestrator.event_pb2 as event_pb2
import orchestrator.failure_report_pb2 as failure_report_pb2
import orchestrator.function_pb2 as function_pb2
import orchestrator.info_pb2 as info_pb2
import orchestrator.model_pb2 as model_pb2
import orchestrator.organization_pb2 as organization_pb2
import orchestrator.performance_pb2 as performance_pb2
import orchestrator.profiling_pb2 as profiling_pb2
from orchestrator.computeplan_pb2_grpc import ComputePlanServiceStub
from orchestrator.computetask_pb2_grpc import ComputeTaskServiceStub
from orchestrator.datamanager_pb2_grpc import DataManagerServiceStub
from orchestrator.datasample_pb2_grpc import DataSampleServiceStub
from orchestrator.dataset_pb2_grpc import DatasetServiceStub
from orchestrator.error import OrcError
from orchestrator.event_pb2_grpc import EventServiceStub
from orchestrator.failure_report_pb2_grpc import FailureReportServiceStub
from orchestrator.function_pb2_grpc import FunctionServiceStub
from orchestrator.info_pb2_grpc import InfoServiceStub
from orchestrator.model_pb2_grpc import ModelServiceStub
from orchestrator.organization_pb2_grpc import OrganizationServiceStub
from orchestrator.performance_pb2_grpc import PerformanceServiceStub
from orchestrator.profiling_pb2_grpc import ProfilingServiceStub
from orchestrator.resources import TAG_KEY
from orchestrator.resources import ComputePlan
from orchestrator.resources import ComputeTask
from orchestrator.resources import ComputeTaskInputAsset
from orchestrator.resources import Function
from orchestrator.resources import OrchestratorVersion

logger = structlog.get_logger(__name__)

GRPC_RETRYABLE_ERRORS = [
    grpc.StatusCode.UNKNOWN,
    grpc.StatusCode.UNAVAILABLE,
]


def add_tag_from_metadata(task: dict) -> None:
    task["tag"] = task["metadata"].pop(TAG_KEY, "")


def grpc_retry(func):
    """Decorator to handle grpc errors from the orchestrator.
    It retries on UNKNOWN or UNAVAILABLE error and wraps the returned error as an OrcError.
    """

    # In case of grpc status code unknown, we retry 5 times spaced by 1s
    @wraps(func)
    def wrapper(*args, **kwargs):
        retry_exception = None
        times = 5
        for attempt in range(times):
            try:
                # We create a copy of the arguments to make sure that mutated arguments are not sent when
                # performing multiple attempts.
                # Since we are in a class the first arg is always self and it can't be copied.
                args_copy = deepcopy(args[1:])
                kwargs_copy = deepcopy(kwargs)

                return func(args[0], *args_copy, **kwargs_copy)
            except grpc.RpcError as rpc_error:
                err = OrcError()
                err.code = grpc.StatusCode(rpc_error.code())
                err.details = rpc_error.details()

                if rpc_error.code() in GRPC_RETRYABLE_ERRORS:
                    retry_exception = err
                    logger.exception(rpc_error)

                    if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
                        sleep_duration = 2 * settings.ORCHESTRATOR_RETRY_DELAY * (attempt + 1)
                    else:
                        sleep_duration = settings.ORCHESTRATOR_RETRY_DELAY

                    logger.info(
                        "grpc.RpcError thrown on orchestrator api request",
                        function=func,
                        attempt=(attempt + 1),
                        max_attempts=times,
                        delay=f"{sleep_duration}s",
                    )

                    time.sleep(sleep_duration)

                else:
                    raise err

        raise retry_exception

    return wrapper


CONVERT_SETTINGS = {
    "preserving_proto_field_name": True,
    "including_default_value_fields": True,
}


class OrchestratorClient:
    def __init__(
        self,
        target,
        channel_name,
        mspid,
        cacert=None,
        client_key=None,
        client_cert=None,
        opts=None,
    ):
        """Construct a grpc channel.
        :param target: server address include host:port
        :param cert_file: ssl/tls root cert file for the connection (Default value = None)
        :param opts: grpc channel options
                    grpc.default_authority: default authority
                    grpc.ssl_target_name_override: ssl target name override
        :param client_key: client key (Default value = None)
        :param client_cert: client certificate (Default value = None)
        :return: grpc channel
        """

        root_cert = None

        if cacert:
            if isinstance(cacert, bytes):
                root_cert = cacert
            else:
                with open(cacert, "rb") as f:
                    root_cert = f.read()

        if client_key:
            if not isinstance(client_key, bytes):
                with open(client_key, "rb") as f:
                    client_key = f.read()

        if client_cert:
            if not isinstance(client_cert, bytes):
                with open(client_cert, "rb") as f:
                    client_cert = f.read()

        if root_cert is None:
            self.grpc_channel = grpc.insecure_channel(target, opts)
        else:
            if client_cert and client_key:
                creds = grpc.ssl_channel_credentials(root_cert, private_key=client_key, certificate_chain=client_cert)
            else:
                creds = grpc.ssl_channel_credentials(root_cert)

            self.grpc_channel = grpc.secure_channel(target, creds, opts)

        self._organization_client = OrganizationServiceStub(self.grpc_channel)
        self._function_client = FunctionServiceStub(self.grpc_channel)
        self._datasample_client = DataSampleServiceStub(self.grpc_channel)
        self._datamanager_client = DataManagerServiceStub(self.grpc_channel)
        self._dataset_client = DatasetServiceStub(self.grpc_channel)
        self._computetask_client = ComputeTaskServiceStub(self.grpc_channel)
        self._computeplan_client = ComputePlanServiceStub(self.grpc_channel)
        self._model_client = ModelServiceStub(self.grpc_channel)
        self._profiling_client = ProfilingServiceStub(self.grpc_channel)
        self._performance_client = PerformanceServiceStub(self.grpc_channel)
        self._event_client = EventServiceStub(self.grpc_channel)
        self._info_client = InfoServiceStub(self.grpc_channel)
        self._failure_report_client = FailureReportServiceStub(self.grpc_channel)
        self._channel_name = channel_name
        self._mspid = mspid

        self._metadata = (
            ("mspid", mspid),
            ("channel", channel_name),
        )

    @property
    def channel_name(self):
        return self._channel_name

    @grpc_retry
    def register_organization(self, args: dict):
        data = self._organization_client.RegisterOrganization(
            organization_pb2.RegisterOrganizationParam(**args), metadata=self._metadata
        )
        MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def register_function(self, args):
        args["inputs"] = {
            identifier: function_pb2.FunctionInput(**_input) for identifier, _input in args["inputs"].items()
        }
        args["outputs"] = {
            identifier: function_pb2.FunctionOutput(**_output) for identifier, _output in args["outputs"].items()
        }
        data = self._function_client.RegisterFunction(function_pb2.NewFunction(**args), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def update_function(self, args):
        data = self._function_client.UpdateFunction(function_pb2.UpdateFunctionParam(**args), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def update_function_status(self, function_key, action):
        data = self._function_client.ApplyFunctionAction(
            function_pb2.ApplyFunctionActionParam(function_key=function_key, action=action),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_function(self, key) -> Function:
        data = self._function_client.GetFunction(function_pb2.GetFunctionParam(key=key), metadata=self._metadata)
        return Function.from_grpc(data)

    @grpc_retry
    def query_functions(self, compute_plan_key=None) -> Generator[Function, None, None]:
        function_filter = function_pb2.FunctionQueryFilter(compute_plan_key=compute_plan_key)
        page_token = ""  # nosec
        while True:
            data = self._function_client.QueryFunctions(
                function_pb2.QueryFunctionsParam(filter=function_filter, page_token=page_token),
                metadata=self._metadata,
            )
            for function in data.Functions:
                yield Function.from_grpc(function)

            page_token = data.next_page_token
            if page_token == "" or len(data.Functions) == 0:  # nosec
                break

    @grpc_retry
    def register_datasamples(self, args):
        data = self._datasample_client.RegisterDataSamples(
            datasample_pb2.RegisterDataSamplesParam(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)["data_samples"]

    @grpc_retry
    def update_datasample(self, args):
        data = self._datasample_client.UpdateDataSamples(
            datasample_pb2.UpdateDataSamplesParam(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def register_datamanager(self, args):
        data = self._datamanager_client.RegisterDataManager(
            datamanager_pb2.NewDataManager(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def update_datamanager(self, args):
        data = self._datamanager_client.UpdateDataManager(
            datamanager_pb2.UpdateDataManagerParam(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    def _get_task_input(self, input: dict) -> computetask_pb2.ComputeTaskInput:
        """Convert a dict into a computetask_pb2.ComputeTaskInput"""

        if input["asset_key"]:
            return computetask_pb2.ComputeTaskInput(
                identifier=input["identifier"],
                asset_key=input["asset_key"],
            )

        return computetask_pb2.ComputeTaskInput(
            identifier=input["identifier"],
            parent_task_output=computetask_pb2.ParentTaskOutputRef(
                parent_task_key=input["parent_task_key"],
                output_identifier=input["parent_task_output_identifier"],
            ),
        )

    @grpc_retry
    def register_tasks(self, args):
        for task in args["tasks"]:
            task["inputs"] = [self._get_task_input(input) for input in task["inputs"]]
            task["outputs"] = {
                identifier: computetask_pb2.NewComputeTaskOutput(
                    permissions=output["permissions"], transient=output.get("transient")
                )
                for identifier, output in task["outputs"].items()
            }
        data = self._computetask_client.RegisterTasks(
            computetask_pb2.RegisterTasksParam(**args), metadata=self._metadata
        )
        data = MessageToDict(data, **CONVERT_SETTINGS)["tasks"]
        for datum in data:
            add_tag_from_metadata(datum)
        return data

    @grpc_retry
    def update_task_status(self, compute_task_key, action, log=""):
        data = self._computetask_client.ApplyTaskAction(
            computetask_pb2.ApplyTaskActionParam(compute_task_key=compute_task_key, action=action, log=log),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    def disable_task_output(self, task_key: str, identifier: str) -> None:
        self._computetask_client.DisableOutput(
            computetask_pb2.DisableOutputParam(compute_task_key=task_key, identifier=identifier),
            metadata=self._metadata,
        )

    @grpc_retry
    def query_task(self, key) -> ComputeTask:
        data = self._computetask_client.GetTask(computetask_pb2.GetTaskParam(key=key), metadata=self._metadata)
        return ComputeTask.from_grpc(data)

    @grpc_retry
    def register_compute_plan(self, args):
        data = self._computeplan_client.RegisterPlan(computeplan_pb2.NewComputePlan(**args), metadata=self._metadata)
        data = MessageToDict(data, **CONVERT_SETTINGS)

        return data

    @grpc_retry
    def update_compute_plan(self, args):
        data = self._computeplan_client.UpdatePlan(
            computeplan_pb2.UpdateComputePlanParam(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_compute_plan(self, key) -> ComputePlan:
        data = self._computeplan_client.GetPlan(computeplan_pb2.GetComputePlanParam(key=key), metadata=self._metadata)
        return ComputePlan.from_grpc(data)

    @grpc_retry
    def cancel_compute_plan(self, key):
        data = self._computeplan_client.ApplyPlanAction(
            computeplan_pb2.ApplyPlanActionParam(key=key, action=computeplan_pb2.PLAN_ACTION_CANCELED),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def is_compute_plan_running(self, key: str) -> bool:
        resp: computeplan_pb2.IsPlanRunningResponse = self._computeplan_client.IsPlanRunning(
            computeplan_pb2.IsPlanRunningParam(key=key), metadata=self._metadata
        )
        return resp.is_running

    @grpc_retry
    def get_computetask_output_models(self, compute_task_key):
        data = self._model_client.GetComputeTaskOutputModels(
            model_pb2.GetComputeTaskModelsParam(compute_task_key=compute_task_key),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS).get("models", [])

    @grpc_retry
    def register_models(self, args):
        data = self._model_client.RegisterModels(model_pb2.RegisterModelsParam(**args), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS).get("models", [])

    @grpc_retry
    def register_performance(self, args):
        data = self._performance_client.RegisterPerformance(
            performance_pb2.NewPerformance(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    def subscribe_to_events(self, channel_name=None, start_event_id=""):
        if channel_name is not None:
            metadata = (
                ("mspid", self._mspid),
                ("channel", channel_name),
            )
        else:
            metadata = self._metadata

        events_stream = self._event_client.SubscribeToEvents(
            event_pb2.SubscribeToEventsParam(start_event_id=start_event_id),
            metadata=metadata,
        )

        return (MessageToDict(event, **CONVERT_SETTINGS) for event in events_stream)

    def query_version(self) -> OrchestratorVersion:
        data = self._info_client.QueryVersion(
            info_pb2.QueryVersionParam(),
            metadata=self._metadata,
        )
        return OrchestratorVersion.from_grpc(data)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.grpc_channel.close()

    @grpc_retry
    def register_failure_report(self, args):
        data = self._failure_report_client.RegisterFailureReport(
            failure_report_pb2.NewFailureReport(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def get_task_input_assets(self, task_key: str) -> list[ComputeTaskInputAsset]:
        assets = self._computetask_client.GetTaskInputAssets(
            computetask_pb2.GetTaskInputAssetsParam(compute_task_key=task_key),
            metadata=self._metadata,
        )
        return [ComputeTaskInputAsset.from_grpc(asset) for asset in assets.assets]

    @grpc_retry
    def register_profiling_step(self, duration: datetime.timedelta, asset_key: str, step: str) -> None:
        duration_micros = duration_microseconds(duration)
        profiling_step = profiling_pb2.ProfilingStep(asset_key=asset_key, duration=duration_micros, step=step)

        self._profiling_client.RegisterProfilingStep(profiling_step, metadata=self._metadata)


def get_orchestrator_client(channel_name: str = None) -> OrchestratorClient:
    host = f"{settings.ORCHESTRATOR_HOST}:{settings.ORCHESTRATOR_PORT}"

    cacert = None
    client_key = None
    client_cert = None

    if settings.ORCHESTRATOR_TLS_ENABLED:
        cacert = settings.ORCHESTRATOR_TLS_SERVER_CACERT_PATH

    if settings.ORCHESTRATOR_MTLS_ENABLED:
        client_key = settings.ORCHESTRATOR_TLS_CLIENT_KEY_PATH
        client_cert = settings.ORCHESTRATOR_TLS_CLIENT_CERT_PATH

    mspid = settings.MSP_ID

    opts = (
        ("grpc.keepalive_time_ms", settings.ORCHESTRATOR_GRPC_KEEPALIVE_TIME_MS),
        ("grpc.keepalive_timeout_ms", settings.ORCHESTRATOR_GRPC_KEEPALIVE_TIMEOUT_MS),
        ("grpc.keepalive_permit_without_calls", settings.ORCHESTRATOR_GRPC_KEEPALIVE_PERMIT_WITHOUT_CALLS),
        ("grpc.http2.max_pings_without_data", settings.ORCHESTRATOR_GRPC_KEEPALIVE_MAX_PINGS_WITHOUT_DATA),
    )

    return OrchestratorClient(host, channel_name, mspid, cacert, client_key, client_cert, opts=opts)
