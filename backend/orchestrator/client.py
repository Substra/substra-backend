import grpc

import structlog
import orchestrator.node_pb2 as node_pb2
import orchestrator.algo_pb2 as algo_pb2
import orchestrator.objective_pb2 as objective_pb2
import orchestrator.datasample_pb2 as datasample_pb2
import orchestrator.datamanager_pb2 as datamanager_pb2
import orchestrator.dataset_pb2 as dataset_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.model_pb2 as model_pb2
import orchestrator.performance_pb2 as performance_pb2
import orchestrator.common_pb2 as common_pb2
import orchestrator.event_pb2 as event_pb2
import orchestrator.info_pb2 as info_pb2
from orchestrator.error import OrcError
from orchestrator.node_pb2_grpc import NodeServiceStub
from orchestrator.algo_pb2_grpc import AlgoServiceStub
from orchestrator.objective_pb2_grpc import ObjectiveServiceStub
from orchestrator.datasample_pb2_grpc import DataSampleServiceStub
from orchestrator.datamanager_pb2_grpc import DataManagerServiceStub
from orchestrator.dataset_pb2_grpc import DatasetServiceStub
from orchestrator.computetask_pb2_grpc import ComputeTaskServiceStub
from orchestrator.computeplan_pb2_grpc import ComputePlanServiceStub
from orchestrator.model_pb2_grpc import ModelServiceStub
from orchestrator.performance_pb2_grpc import PerformanceServiceStub
from orchestrator.event_pb2_grpc import EventServiceStub
from orchestrator.info_pb2_grpc import InfoServiceStub
from google.protobuf.json_format import MessageToDict

import time
from functools import wraps

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
                        delay=f"{sleep_duration}s"
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
                creds = grpc.ssl_channel_credentials(
                    root_cert, private_key=client_key, certificate_chain=client_cert
                )
            else:
                creds = grpc.ssl_channel_credentials(root_cert)

            self._channel = grpc.secure_channel(target, creds, opts)

        self._node_client = NodeServiceStub(self._channel)
        self._algo_client = AlgoServiceStub(self._channel)
        self._objective_client = ObjectiveServiceStub(self._channel)
        self._datasample_client = DataSampleServiceStub(self._channel)
        self._datamanager_client = DataManagerServiceStub(self._channel)
        self._dataset_client = DatasetServiceStub(self._channel)
        self._computetask_client = ComputeTaskServiceStub(self._channel)
        self._computeplan_client = ComputePlanServiceStub(self._channel)
        self._model_client = ModelServiceStub(self._channel)
        self._performance_client = PerformanceServiceStub(self._channel)
        self._event_client = EventServiceStub(self._channel)
        self._info_client = InfoServiceStub(self._channel)

        self._metadata = (
            ("mspid", mspid),
            ("channel", channel_name),
            ("chaincode", chaincode),
        )

    @grpc_retry
    def register_node(self):
        data = self._node_client.RegisterNode(
            node_pb2.RegisterNodeParam(), metadata=self._metadata
        )
        MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_nodes(self):
        data = self._node_client.GetAllNodes(
            node_pb2.GetAllNodesParam(), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS).get("nodes", [])

    @grpc_retry
    def register_algo(self, args):
        data = self._algo_client.RegisterAlgo(
            algo_pb2.NewAlgo(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_algo(self, key):
        data = self._algo_client.GetAlgo(
            algo_pb2.GetAlgoParam(key=key), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_algos(self, category=algo_pb2.ALGO_UNKNOWN, compute_plan_key=None):
        algo_filter = algo_pb2.AlgoQueryFilter(
            category=category, compute_plan_key=compute_plan_key
        )
        res = []
        page_token = ""
        while True:
            data = self._algo_client.QueryAlgos(
                algo_pb2.QueryAlgosParam(filter=algo_filter, page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            algos = data.get("Algos", [])
            page_token = data.get("next_page_token")
            res.extend(algos)
            if page_token == "" or not algos:
                break
        return res

    @grpc_retry
    def register_objective(self, args):
        data = self._objective_client.RegisterObjective(
            objective_pb2.NewObjective(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_objective(self, key):
        data = self._objective_client.GetObjective(
            objective_pb2.GetObjectiveParam(key=key), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_objectives(self):
        res = []
        page_token = ""
        while True:
            data = self._objective_client.QueryObjectives(
                objective_pb2.QueryObjectivesParam(page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            objectives = data.get("objectives", [])
            page_token = data.get("next_page_token")
            res.extend(objectives)
            if page_token == "" or not objectives:
                break
        return res

    @grpc_retry
    def query_objective_leaderboard(self, key, sort="desc"):
        data = self._objective_client.GetLeaderboard(
            objective_pb2.LeaderboardQueryParam(
                objective_key=key, sort_order=SORT_ORDER[sort]
            ),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def register_datasamples(self, args):
        data = self._datasample_client.RegisterDataSamples(
            datasample_pb2.RegisterDataSamplesParam(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def update_datasample(self, args):
        data = self._datasample_client.UpdateDataSamples(
            datasample_pb2.UpdateDataSamplesParam(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_datasamples(self):
        res = []
        page_token = ""
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
            if page_token == "" or not data_samples:
                break
        return res

    @grpc_retry
    def register_datamanager(self, args):
        data = self._datamanager_client.RegisterDataManager(
            datamanager_pb2.NewDataManager(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def update_datamanager(self, args):
        data = self._datamanager_client.UpdateDataManager(
            datamanager_pb2.DataManagerUpdateParam(**args), metadata=self._metadata
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
        data = self._dataset_client.GetDataset(
            dataset_pb2.GetDatasetParam(key=key), metadata=self._metadata
        )
        data = MessageToDict(data, **CONVERT_SETTINGS)

        # process dataset result to have data_manager attibutes at
        # top level
        data.update(data["data_manager"])
        del data["data_manager"]
        return data

    @grpc_retry
    def query_datamanagers(self):
        res = []
        page_token = ""
        while True:
            data = self._datamanager_client.QueryDataManagers(
                datamanager_pb2.QueryDataManagersParam(page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            data_managers = data.get("data_managers", [])
            page_token = data.get("next_page_token")
            res.extend(data_managers)
            if page_token == "" or not data_managers:
                break
        return res

    @grpc_retry
    def register_tasks(self, args):
        data = self._computetask_client.RegisterTasks(
            computetask_pb2.RegisterTasksParam(**args), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def update_task_status(self, compute_task_key, action, log=""):
        data = self._computetask_client.ApplyTaskAction(
            computetask_pb2.ApplyTaskActionParam(
                compute_task_key=compute_task_key, action=action, log=log
            ),
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
        page_token = ""
        while True:
            data = self._computetask_client.QueryTasks(
                computetask_pb2.QueryTasksParam(
                    filter=task_filter, page_token=page_token
                ),
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
            if page_token == "" or not tasks:
                break
        return res

    @grpc_retry
    def query_task(self, key):
        data = self._computetask_client.GetTask(
            computetask_pb2.GetTaskParam(key=key), metadata=self._metadata
        )
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
        data = self._computeplan_client.RegisterPlan(
            computeplan_pb2.NewComputePlan(**args), metadata=self._metadata
        )
        data = MessageToDict(data, **CONVERT_SETTINGS)

        return data

    @grpc_retry
    def _add_compute_plan_failed_task(self, data):
        """Private method to add the first failed task information to a compute plan data.
        It helps the final user to find which task failed the compute plan.
        """

        if computeplan_pb2.ComputePlanStatus.Value(data["status"]) == computeplan_pb2.PLAN_STATUS_FAILED:
            # Add failed task if any
            failed_tasks = self.query_tasks(status=computetask_pb2.STATUS_FAILED, compute_plan_key=data['key'])

            # Fetch event timestamp of failure to sort failed tasks in order to get the first failed task
            if len(failed_tasks):
                failed_timestamps = []
                for failed_task in failed_tasks:
                    failed_events = self.query_events(
                        asset_key=failed_task["key"],
                        event_kind=event_pb2.EVENT_ASSET_UPDATED,
                    )
                    for failed_event in failed_events:
                        if failed_event["metadata"]["status"] == "STATUS_FAILED":
                            failed_timestamps.append(failed_event["timestamp"])

                if len(failed_timestamps) == len(failed_tasks):
                    failed_tasks = zip(failed_timestamps, failed_tasks)
                    # The lambda expr is used to avoid an exception on dict sorting when timestamps are equal
                    failed_tasks = [
                        x for _, x in sorted(failed_tasks, key=lambda tup: tup[0])
                    ]

                data['failed_task'] = {}
                data['failed_task']['key'] = failed_tasks[0]['key']
                data['failed_task']['category'] = failed_tasks[0]['category']
        else:
            data['failed_task'] = None

        return data

    @grpc_retry
    def query_compute_plan(self, key):
        data = self._computeplan_client.GetPlan(
            computeplan_pb2.GetComputePlanParam(key=key), metadata=self._metadata
        )
        data = MessageToDict(data, **CONVERT_SETTINGS)
        data = self._add_compute_plan_failed_task(data)

        return data

    @grpc_retry
    def cancel_compute_plan(self, key):
        data = self._computeplan_client.ApplyPlanAction(
            computeplan_pb2.ApplyPlanActionParam(
                key=key, action=computeplan_pb2.PLAN_ACTION_CANCELED
            ),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_compute_plans(self):
        res = []
        page_token = ""
        while True:
            data = self._computeplan_client.QueryPlans(
                computeplan_pb2.QueryPlansParam(page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            plans = data.get("plans", [])
            page_token = data.get("next_page_token")

            for plan in plans:
                plan = self._add_compute_plan_failed_task(plan)

            res.extend(plans)
            if page_token == "" or not plans:
                break
        return res

    @grpc_retry
    def query_model(self, key):
        data = self._model_client.GetModel(
            model_pb2.GetModelParam(key=key), metadata=self._metadata
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def query_models(self, category=algo_pb2.ALGO_UNKNOWN):

        res = []
        page_token = ""
        while True:
            data = self._model_client.QueryModels(
                model_pb2.QueryModelsParam(category=category, page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            models = data.get("models", [])
            page_token = data.get("next_page_token")
            res.extend(models)
            if page_token == "" or not models:
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
        data = self._model_client.RegisterModel(
            model_pb2.NewModel(**args), metadata=self._metadata
        )
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
    def get_compute_task_performance(self, compute_task_key):
        data = self._performance_client.GetComputeTaskPerformance(
            performance_pb2.GetComputeTaskPerformanceParam(
                compute_task_key=compute_task_key
            ),
            metadata=self._metadata,
        )
        return MessageToDict(data, **CONVERT_SETTINGS)

    @grpc_retry
    def is_task_doing(self, key):
        task = self.query_task(key)
        return (
            computetask_pb2.ComputeTaskStatus.Value(task["status"]) == computetask_pb2.STATUS_DOING
        )

    @grpc_retry
    def is_task_in_final_state(self, key):
        task = self.query_task(key)
        return computetask_pb2.ComputeTaskStatus.Value(task["status"]) in [
            computetask_pb2.STATUS_CANCELED,
            computetask_pb2.STATUS_DONE,
            computetask_pb2.STATUS_FAILED
        ]

    @grpc_retry
    def is_compute_plan_doing(self, key):
        cp = self.query_compute_plan(key)
        return (
            computeplan_pb2.ComputePlanStatus.Value(cp["status"]) == computeplan_pb2.PLAN_STATUS_DOING
        )

    @grpc_retry
    def query_events(
        self,
        asset_key="",
        asset_kind=common_pb2.ASSET_UNKNOWN,
        event_kind=event_pb2.EVENT_UNKNOWN,
    ):
        event_filter = event_pb2.EventQueryFilter(
            asset_key=asset_key, asset_kind=asset_kind, event_kind=event_kind
        )

        res = []
        page_token = ""
        while True:
            data = self._event_client.QueryEvents(
                event_pb2.QueryEventsParam(filter=event_filter, page_token=page_token),
                metadata=self._metadata,
            )
            data = MessageToDict(data, **CONVERT_SETTINGS)
            events = data.get("events", [])
            page_token = data.get("next_page_token")
            res.extend(events)
            if page_token == "" or not events:
                break

        return res

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
