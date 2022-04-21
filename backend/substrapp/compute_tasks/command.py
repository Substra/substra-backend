import json
import os
from typing import List

import structlog

import orchestrator.algo_pb2 as algo_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.model_pb2 as model_pb2
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import SANDBOX_DIR
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.compute_tasks.transfer_bucket import TAG_VALUE_FOR_TRANSFER_BUCKET
from substrapp.compute_tasks.transfer_bucket import TRANSFER_BUCKET_TESTTUPLE_TAG
from substrapp.models.image_entrypoint import ImageEntrypoint

logger = structlog.get_logger(__name__)

# These constants are shared with connect-tools.
# These constants will disappear once the inputs/outputs are exposed by the orchestrator.
TASK_IO_PREDICTIONS = "predictions"
TASK_IO_OPENER = "opener"
TASK_IO_LOCALFOLDER = "localfolder"
TASK_IO_CHAINKEYS = "chainkeys"
TASK_IO_DATASAMPLES = "datasamples"
TRAIN_IO_MODELS = "models"
TRAIN_IO_MODEL = "model"
COMPOSITE_IO_SHARED = "shared"
COMPOSITE_IO_LOCAL = "local"


class Filenames:
    OutModel = "out-model"
    OutHeadModel = "out-head-model"
    Opener = "__init__.py"
    Predictions = "pred.json"
    Performance = "perf.json"


TASK_COMMANDS = {
    computetask_pb2.TASK_TRAIN: "train",
    computetask_pb2.TASK_TEST: "predict",
    computetask_pb2.TASK_COMPOSITE: "train",
    computetask_pb2.TASK_AGGREGATE: "aggregate",
}


def get_exec_command(ctx: Context, is_testtuple_eval: bool, metric_key: str = None) -> List[str]:

    if is_testtuple_eval:
        entrypoint = ImageEntrypoint.objects.get(asset_key=metric_key)
    else:
        entrypoint = ImageEntrypoint.objects.get(asset_key=ctx.algo_key)

    command = json.loads(entrypoint.entrypoint_json)

    if command[0].startswith("python"):
        command.insert(1, "-u")  # unbuffered. Allows streaming the logs in real-time.

    env = _get_env(ctx, is_testtuple_eval)
    args = _get_args(ctx, is_testtuple_eval, metric_key)

    return env + command + args


class TaskResource(dict):

    # By inheriting from dict, we get JSON serialization for free
    def __init__(self, id: str, value: str):
        dict.__init__(self, id=id, value=value)


# TODO: '_get_args' is too complex, consider refactoring
def _get_args(ctx: Context, is_testtuple_eval: bool, metric_key: str = None) -> List[str]:  # noqa: C901
    task = ctx.task
    task_category = ctx.task_category
    task_data = ctx.task_data
    algo_cat = algo_pb2.AlgoCategory.Value(ctx.algo["category"])

    in_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.InModels)
    out_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.OutModels)
    openers_dir = os.path.join(SANDBOX_DIR, TaskDirName.Openers)
    datasamples_dir = os.path.join(SANDBOX_DIR, TaskDirName.Datasamples)
    pred_path = os.path.join(SANDBOX_DIR, TaskDirName.Pred, Filenames.Predictions)
    local_folder = os.path.join(SANDBOX_DIR, TaskDirName.Local)
    chainkeys_folder = os.path.join(SANDBOX_DIR, TaskDirName.Chainkeys)

    inputs = []
    outputs = []

    if is_testtuple_eval:
        perf_path = os.path.join(SANDBOX_DIR, TaskDirName.Perf, "-".join([metric_key, Filenames.Performance]))
        command = ["--input-predictions-path", pred_path]
        command += ["--opener-path", os.path.join(openers_dir, task_data["data_manager_key"], Filenames.Opener)]
        command += ["--data-sample-paths"] + [
            os.path.join(datasamples_dir, key) for key in task_data["data_sample_keys"]
        ]
        command += ["--output-perf-path", perf_path]
        return command

    compute_plan_key = None
    if "compute_plan_key" in task and task["compute_plan_key"]:
        compute_plan_key = task["compute_plan_key"]
    rank = str(task["rank"]) if compute_plan_key else None

    command = [TASK_COMMANDS[task_category]]

    if task_category == computetask_pb2.TASK_TRAIN:

        if ctx.in_models:
            inputs.extend(
                [
                    TaskResource(id=TRAIN_IO_MODELS, value=os.path.join(in_models_dir, model["key"]))
                    for model in ctx.in_models
                ]
            )

        inputs.append(
            TaskResource(
                id=TASK_IO_OPENER, value=os.path.join(openers_dir, task_data["data_manager_key"], Filenames.Opener)
            )
        )
        for key in task_data["data_sample_keys"]:
            inputs.append(TaskResource(id=TASK_IO_DATASAMPLES, value=os.path.join(datasamples_dir, key)))
        outputs.append(TaskResource(id=TRAIN_IO_MODEL, value=os.path.join(out_models_dir, Filenames.OutModel)))
        outputs.append(TaskResource(id=TASK_IO_LOCALFOLDER, value=local_folder))

    elif task_category == computetask_pb2.TASK_COMPOSITE:

        for input_model in ctx.in_models:
            cat = model_pb2.ModelCategory.Value(input_model["category"])
            if cat == model_pb2.MODEL_HEAD:
                inputs.append(
                    TaskResource(id=COMPOSITE_IO_LOCAL, value=os.path.join(in_models_dir, input_model["key"]))
                )
            elif cat == model_pb2.MODEL_SIMPLE:
                inputs.append(
                    TaskResource(id=COMPOSITE_IO_SHARED, value=os.path.join(in_models_dir, input_model["key"]))
                )

        inputs.append(
            TaskResource(
                id=TASK_IO_OPENER, value=os.path.join(openers_dir, task_data["data_manager_key"], Filenames.Opener)
            )
        )
        for key in task_data["data_sample_keys"]:
            inputs.append(TaskResource(id=TASK_IO_DATASAMPLES, value=os.path.join(datasamples_dir, key)))
        outputs.append(TaskResource(id=COMPOSITE_IO_LOCAL, value=os.path.join(out_models_dir, Filenames.OutHeadModel)))
        outputs.append(TaskResource(id=COMPOSITE_IO_SHARED, value=os.path.join(out_models_dir, Filenames.OutModel)))
        outputs.append(TaskResource(id=TASK_IO_LOCALFOLDER, value=local_folder))

    elif task_category == computetask_pb2.TASK_AGGREGATE:
        if ctx.in_models:
            inputs.extend(
                [
                    TaskResource(id=TRAIN_IO_MODELS, value=os.path.join(in_models_dir, model["key"]))
                    for model in ctx.in_models
                ]
            )

        outputs.append(TaskResource(id=TRAIN_IO_MODEL, value=os.path.join(out_models_dir, Filenames.OutModel)))
        outputs.append(TaskResource(id=TASK_IO_LOCALFOLDER, value=local_folder))

    elif task_category == computetask_pb2.TASK_TEST:

        if algo_cat == algo_pb2.ALGO_COMPOSITE:
            for input_model in ctx.in_models:
                model_cat = model_pb2.ModelCategory.Value(input_model["category"])

                if model_cat == model_pb2.MODEL_HEAD:
                    inputs.append(
                        TaskResource(id=COMPOSITE_IO_LOCAL, value=os.path.join(in_models_dir, input_model["key"]))
                    )
                elif model_cat == model_pb2.MODEL_SIMPLE:
                    inputs.append(
                        TaskResource(id=COMPOSITE_IO_SHARED, value=os.path.join(in_models_dir, input_model["key"]))
                    )
        else:
            inputs.extend(
                [
                    TaskResource(id=TRAIN_IO_MODELS, value=os.path.join(in_models_dir, input_model["key"]))
                    for input_model in ctx.in_models
                ]
            )

        inputs.append(
            TaskResource(
                id=TASK_IO_OPENER, value=os.path.join(openers_dir, task_data["data_manager_key"], Filenames.Opener)
            )
        )
        for key in task_data["data_sample_keys"]:
            inputs.append(TaskResource(id=TASK_IO_DATASAMPLES, value=os.path.join(datasamples_dir, key)))
        outputs.append(TaskResource(id=TASK_IO_PREDICTIONS, value=pred_path))
        outputs.append(TaskResource(id=TASK_IO_LOCALFOLDER, value=local_folder))

    if rank and task_category != computetask_pb2.TASK_TEST:
        command += ["--rank", rank]
    if ctx.has_chainkeys:
        inputs.append(TaskResource(id=TASK_IO_CHAINKEYS, value=chainkeys_folder))

    command += ["--inputs", f"'{json.dumps(inputs)}'"]
    command += ["--outputs", f"'{json.dumps(outputs)}'"]

    logger.debug("Generated task command", command=command)

    return command


def _get_env(ctx: Context, is_testtuple_eval: bool) -> List[str]:
    """This return environment variables for the task"""

    env = []

    # Transfer bucket
    tag = ctx.task.get("tag")
    if ctx.task_category == computetask_pb2.TASK_TEST and not is_testtuple_eval:
        if tag and TAG_VALUE_FOR_TRANSFER_BUCKET in tag:
            env.append(f"{TRANSFER_BUCKET_TESTTUPLE_TAG}={TAG_VALUE_FOR_TRANSFER_BUCKET}")

    return env
