import time
from functools import wraps

import grpc
import structlog
from google.protobuf.json_format import MessageToDict
from google.protobuf.timestamp_pb2 import Timestamp

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.common_pb2 as common_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.datamanager_pb2 as datamanager_pb2
import orchestrator.datasample_pb2 as datasample_pb2
import orchestrator.dataset_pb2 as dataset_pb2
import orchestrator.event_pb2 as event_pb2
import orchestrator.failure_report_pb2 as failure_report_pb2
import orchestrator.info_pb2 as info_pb2
import orchestrator.metric_pb2 as metric_pb2
import orchestrator.model_pb2 as model_pb2
import orchestrator.node_pb2 as node_pb2
import orchestrator.performance_pb2 as performance_pb2
from orchestrator.algo_pb2_grpc import AlgoServiceStub
from orchestrator.computeplan_pb2_grpc import ComputePlanServiceStub
from orchestrator.computetask_pb2_grpc import ComputeTaskServiceStub
from orchestrator.datamanager_pb2_grpc import DataManagerServiceStub
from orchestrator.datasample_pb2_grpc import DataSampleServiceStub
from orchestrator.dataset_pb2_grpc import DatasetServiceStub
from orchestrator.error import OrcError
from orchestrator.event_pb2_grpc import EventServiceStub
from orchestrator.failure_report_pb2_grpc import FailureReportServiceStub
from orchestrator.info_pb2_grpc import InfoServiceStub
from orchestrator.metric_pb2_grpc import MetricServiceStub
from orchestrator.model_pb2_grpc import ModelServiceStub
from orchestrator.node_pb2_grpc import NodeServiceStub
from orchestrator.performance_pb2_grpc import PerformanceServiceStub

logger = structlog.get_logger(__name__)

GRPC_RETRYABLE_ERRORS = [
    grpc.StatusCode.UNKNOWN,
    grpc.StatusCode.UNAVAILABLE,
]


def grpc_retry(func):
    """Decorator to handle grpc errors from the orchestrator.
    It retries on UNKNOWN or UNAVAILABLE error and wraps the returned error as an OrcError.
    """
    # In case of grpc status code unknow, we retry 5 times spaced by 1s
    @wraps(func)
    def wrapper(*args, **kwargs):
        retry_exception = None
        times = 5
        for attempt in range(times):
            try:
                return func(*args, **kwargs)
            except grpc.RpcError as rpc_error:

                err = OrcError()
                err.code = grpc.StatusCode(rpc_error.code())
                err.details = rpc_error.details()

                if rpc_error.code() in GRPC_RETRYABLE_ERRORS:
                    retry_exception = err
                    logger.exception(rpc_error)

                    if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
                        sleep_duration = 2 * (attempt + 1)
                    else:
                        sleep_duration = 1

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

SORT_ORDER = {"asc": common_pb2.ASCENDING, "desc": common_pb2.DESCENDING}


class OrchestratorClient:
    def __init__(
        self,
        target,
        channel_name,
        mspid,
        chaincode,
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
            self._channel = grpc.insecure_channel(target, opts)
        else:
            if client_cert and client_key:
                creds = grpc.ssl_channel_credentials(root_cert, private_key=client_key, certificate_chain=client_cert)
            else:
                creds = grpc.ssl_channel_credentials(root_cert)

            self._channel = grpc.secure_channel(target, creds, opts)

        self._node_client = NodeServiceStub(self._channel)
        self._algo_client = AlgoServiceStub(self._channel)
        self._metric_client = MetricServiceStub(self._channel)
        self._datasample_client = DataSampleServiceStub(self._channel)
        self._datamanager_client = DataManagerServiceStub(self._channel)
        self._dataset_client = DatasetServiceStub(self._channel)
        self._computetask_client = ComputeTaskServiceStub(self._channel)
        self._computeplan_client = ComputePlanServiceStub(self._channel)
        self._model_client = ModelServiceStub(self._channel)
        self._performance_client = PerformanceServiceStub(self._channel)
        self._event_client = EventServiceStub(self._channel)
        self._info_client = InfoServiceStub(self._channel)
        self._failure_report_client = FailureReportServiceStub(self._channel)

        self._metadata = (
            ("mspid", mspid),
            ("channel", channel_name),
            ("chaincode", chaincode),
        )

    @grpc_retry
    def register_node(self):
        data = self._node_client.RegisterNode(node_pb2.RegisterNodeParam(), metadata=self._metadata)
        MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_nodes(self):
        data = self._node_client.GetAllNodes(node_pb2.GetAllNodesParam(), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS).get("nodes", [])

    @grpc_retry
    def register_algo(self, args):
        data = self._algo_client.RegisterAlgo(algo_pb2.NewAlgo(**args), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_algo(self, key):
        data = self._algo_client.GetAlgo(algo_pb2.GetAlgoParam(key=key), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_algos(self, category=algo_pb2.ALGO_UNKNOWN, compute_plan_key=None):
        algo_filter = algo_pb2.AlgoQueryFilter(category=category, compute_plan_key=compute_plan_key)
        res = []
        page_token = ""  # nosec
        while True:
            data = self._algo_client.QueryAlgos(
                algo_pb2.QueryAlgosParam(filter=algo_filter, page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            algos = data.get("Algos", [])
            page_token = data.get("next_page_token")
            res.extend(algos)
            if page_token == "" or not algos:  # nosec
                break
        return res

    @grpc_retry
    def register_metric(self, args):
        data = self._metric_client.RegisterMetric(metric_pb2.NewMetric(**args), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_metric(self, key):
        data = self._metric_client.GetMetric(metric_pb2.GetMetricParam(key=key), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_metrics(self):
        res = []
        page_token = ""  # nosec
        while True:
            data = self._metric_client.QueryMetrics(
                metric_pb2.QueryMetricsParam(page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            metrics = data.get("metrics", [])
            page_token = data.get("next_page_token")
            res.extend(metrics)
            if page_token == "" or not metrics:  # nosec
                break
        return res

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
    def query_datasamples(self):
        res = []
        page_token = ""  # nosec
        while True:
            data = self._datasample_client.QueryDataSamples(
                datasample_pb2.QueryDataSamplesParam(page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            data_samples = data.get("data_samples", [])
            page_token = data.get("next_page_token")
            # For now do not expose sample checksum
            for sample in data_samples:
                del sample["checksum"]
            res.extend(data_samples)
            if page_token == "" or not data_samples:  # nosec
                break
        return res

    @grpc_retry
    def query_datasample(self, key):
        data = self._datasample_client.GetDataSample(
            datasample_pb2.GetDataSampleParam(key=key), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def register_datamanager(self, args):
        data = self._datamanager_client.RegisterDataManager(
            datamanager_pb2.NewDataManager(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_datamanager(self, key):
        data = self._datamanager_client.GetDataManager(
            datamanager_pb2.GetDataManagerParam(key=key), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_dataset(self, key):
        data = self._dataset_client.GetDataset(dataset_pb2.GetDatasetParam(key=key), metadata=self._metadata)
        data = MessageToDict(data, **CONVERT_SETTINGS)

        # process dataset result to have data_manager attibutes at
        # top level
        data.update(data["data_manager"])
        del data["data_manager"]
        return data

    @grpc_retry
    def query_datamanagers(self):
        res = []
        page_token = ""  # nosec
        while True:
            data = self._datamanager_client.QueryDataManagers(
                datamanager_pb2.QueryDataManagersParam(page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            data_managers = data.get("data_managers", [])
            page_token = data.get("next_page_token")
            res.extend(data_managers)
            if page_token == "" or not data_managers:  # nosec
                break
        return res

    @grpc_retry
    def register_tasks(self, args):
        data = self._computetask_client.RegisterTasks(
            computetask_pb2.RegisterTasksParam(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)["tasks"]

    @grpc_retry
    def update_task_status(self, compute_task_key, action, log=""):
        data = self._computetask_client.ApplyTaskAction(
            computetask_pb2.ApplyTaskActionParam(compute_task_key=compute_task_key, action=action, log=log),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_tasks(
        self,
        worker=None,
        status=computetask_pb2.STATUS_UNKNOWN,
        category=computetask_pb2.TASK_UNKNOWN,
        compute_plan_key=None,
    ):
        task_filter = computetask_pb2.TaskQueryFilter(
            worker=worker,
            status=status,
            category=category,
            compute_plan_key=compute_plan_key,
        )

        res = []
        page_token = ""  # nosec
        while True:
            data = self._computetask_client.QueryTasks(
                computetask_pb2.QueryTasksParam(filter=task_filter, page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            tasks = data.get("tasks", [])
            page_token = data.get("next_page_token")
            # handle tag
            for datum in tasks:
                tag = ""
                if "__tag__" in datum["metadata"]:
                    tag = datum["metadata"]["__tag__"]
                    del datum["metadata"]["__tag__"]
                datum["tag"] = tag
            res.extend(tasks)
            if page_token == "" or not tasks:  # nosec
                break
        return res

    @grpc_retry
    def query_task(self, key):
        data = self._computetask_client.GetTask(computetask_pb2.GetTaskParam(key=key), metadata=self._metadata)
        data = MessageToDict(data, **CONVERT_SETTINGS)

        # handle tag
        tag = ""
        if "__tag__" in data["metadata"]:
            tag = data["metadata"]["__tag__"]
            del data["metadata"]["__tag__"]
        data["tag"] = tag
        return data

    @grpc_retry
    def register_compute_plan(self, args):
        data = self._computeplan_client.RegisterPlan(computeplan_pb2.NewComputePlan(**args), metadata=self._metadata)
        data = MessageToDict(data, **CONVERT_SETTINGS)

        return data

    @grpc_retry
    def query_compute_plan(self, key):
        data = self._computeplan_client.GetPlan(computeplan_pb2.GetComputePlanParam(key=key), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def cancel_compute_plan(self, key):
        data = self._computeplan_client.ApplyPlanAction(
            computeplan_pb2.ApplyPlanActionParam(key=key, action=computeplan_pb2.PLAN_ACTION_CANCELED),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_compute_plans(self, owner=None):
        plan_filter = computeplan_pb2.PlanQueryFilter(owner=owner)
        res = []
        page_token = ""  # nosec
        while True:
            data = self._computeplan_client.QueryPlans(
                computeplan_pb2.QueryPlansParam(filter=plan_filter, page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            plans = data.get("plans", [])
            page_token = data.get("next_page_token")

            res.extend(plans)
            if page_token == "" or not plans:  # nosec
                break
        return res

    @grpc_retry
    def query_model(self, key):
        data = self._model_client.GetModel(model_pb2.GetModelParam(key=key), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_models(self, category=algo_pb2.ALGO_UNKNOWN):

        res = []
        page_token = ""  # nosec
        while True:
            data = self._model_client.QueryModels(
                model_pb2.QueryModelsParam(category=category, page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            models = data.get("models", [])
            page_token = data.get("next_page_token")
            res.extend(models)
            if page_token == "" or not models:  # nosec
                break
        return res

    @grpc_retry
    def get_computetask_input_models(self, compute_task_key):
        data = self._model_client.GetComputeTaskInputModels(
            model_pb2.GetComputeTaskModelsParam(compute_task_key=compute_task_key),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS).get("models", [])

    @grpc_retry
    def get_computetask_output_models(self, compute_task_key):
        data = self._model_client.GetComputeTaskOutputModels(
            model_pb2.GetComputeTaskModelsParam(compute_task_key=compute_task_key),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS).get("models", [])

    @grpc_retry
    def register_model(self, args):
        data = self._model_client.RegisterModel(model_pb2.NewModel(**args), metadata=self._metadata)
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def can_disable_model(self, model_key):
        data = self._model_client.CanDisableModel(
            model_pb2.CanDisableModelParam(model_key=model_key), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS).get("can_disable")

    @grpc_retry
    def disable_model(self, model_key):
        data = self._model_client.DisableModel(
            model_pb2.DisableModelParam(model_key=model_key), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def register_performance(self, args):
        data = self._performance_client.RegisterPerformance(
            performance_pb2.NewPerformance(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def get_compute_task_performances(self, compute_task_key, metric_key=""):
        performance_filter = performance_pb2.PerformanceQueryFilter(
            compute_task_key=compute_task_key, metric_key=metric_key
        )

        res = []
        page_token = ""  # nosec
        while True:
            data = self._performance_client.QueryPerformances(
                performance_pb2.QueryPerformancesParam(filter=performance_filter, page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            performances = data.get("Performances", [])
            page_token = data.get("next_page_token")
            res.extend(performances)
            if page_token == "" or not performances:  # nosec
                break

        return res

    @grpc_retry
    def is_compute_plan_doing(self, key):
        cp = self.query_compute_plan(key)
        return computeplan_pb2.ComputePlanStatus.Value(cp["status"]) == computeplan_pb2.PLAN_STATUS_DOING

    def query_events(
        self,
        asset_key="",
        asset_kind=common_pb2.ASSET_UNKNOWN,
        event_kind=event_pb2.EVENT_UNKNOWN,
        sort=common_pb2.ASCENDING,
        metadata=None,
        start=None,
        end=None,
        page_size=None,
    ):
        """return a list with all events instead of a generator"""
        return list(
            self.query_events_generator(
                asset_key=asset_key,
                asset_kind=asset_kind,
                event_kind=event_kind,
                sort=sort,
                metadata=metadata,
                start=start,
                end=end,
                page_size=page_size,
            )
        )

    @grpc_retry
    def query_events_generator(
        self,
        asset_key="",
        asset_kind=common_pb2.ASSET_UNKNOWN,
        event_kind=event_pb2.EVENT_UNKNOWN,
        sort=common_pb2.ASCENDING,
        metadata=None,
        start=None,
        end=None,
        page_size=1,
    ):
        """This function returns all events as a generator.
        Until page_token is null or no more events are fetched, a loop call will get page_size events
        which are yield one by one

        XXX: default page size is 1, which has very bad performance when querying lots of assets.
        """

        # convert JsonStringDate into pb Timestamp
        start_ts = None
        end_ts = None

        if start is not None:
            start_ts = Timestamp()
            start_ts.FromJsonString(start)

        if end is not None:
            end_ts = Timestamp()
            end_ts.FromJsonString(end)

        event_filter = event_pb2.EventQueryFilter(
            asset_key=asset_key,
            asset_kind=asset_kind,
            event_kind=event_kind,
            metadata=metadata,
            start=start_ts,
            end=end_ts,
        )

        page_token = ""  # nosec

        while True:
            data = self._event_client.QueryEvents(
                event_pb2.QueryEventsParam(filter=event_filter, page_token=page_token, page_size=page_size, sort=sort),
                metadata=self._metadata,
            )

            data = MessageToDict(data, **CONVERT_SETTINGS)
            page_token = data.get("next_page_token")
            events = data.get("events", [])

            for event in events:
                yield event

            if page_token == "" or not events:  # nosec
                return

    def query_single_event(
        self,
        asset_key="",
        asset_kind=common_pb2.ASSET_UNKNOWN,
        event_kind=event_pb2.EVENT_UNKNOWN,
        sort=common_pb2.ASCENDING,
        metadata=None,
    ):
        event_generator = self.query_events_generator(
            asset_key=asset_key, asset_kind=asset_kind, event_kind=event_kind, sort=sort, metadata=metadata, page_size=1
        )
        return next(event_generator, None)

    def query_version(
        self,
    ):
        data = self._info_client.QueryVersion(
            info_pb2.QueryVersionParam(),
            metadata=self._metadata,
        )
        data = MessageToDict(data, **CONVERT_SETTINGS)
        return data

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._channel.close()

    @grpc_retry
    def register_failure_report(self, args):
        data = self._failure_report_client.RegisterFailureReport(
            failure_report_pb2.NewFailureReport(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def get_failure_report(self, args):
        data = self._failure_report_client.GetFailureReport(
            failure_report_pb2.GetFailureReportParam(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)
