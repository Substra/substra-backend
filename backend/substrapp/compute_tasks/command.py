import os
import json
from typing import List
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import TaskDirName, SANDBOX_DIR
import substrapp.orchestrator.computetask_pb2 as computetask_pb2
import substrapp.orchestrator.model_pb2 as model_pb2
import substrapp.orchestrator.algo_pb2 as algo_pb2
import logging

logger = logging.getLogger(__name__)


class Filenames:
    OutModel = "out-model"
    OutHeadModel = "out-head-model"
    OutTrunkModel = "out-trunk-model"
    Opener = "__init__.py"
    Predictions = "pred.json"
    Performance = "perf.json"


TASK_COMMANDS = {
    computetask_pb2.TASK_TRAIN: "train",
    computetask_pb2.TASK_TEST: "predict",
    computetask_pb2.TASK_COMPOSITE: "train",
    computetask_pb2.TASK_AGGREGATE: "aggregate",
}


def get_exec_command(ctx: Context, is_testtuple_eval: bool) -> List[str]:

    docker_context_dir = ctx.metrics_docker_context_dir if is_testtuple_eval else ctx.algo_docker_context_dir

    command = _get_command_from_dockerfile(docker_context_dir)
    if command[0].startswith("python"):
        command.insert(1, "-u")  # unbuffered. Allows streaming the logs in real-time.

    args = _get_args(ctx, is_testtuple_eval)
    return command + args


def _get_command_from_dockerfile(dockerfile_dir: str) -> List[str]:
    """
    Extract command from ENTRYPOINT in the Dockerfile.

    This is necessary because the user algo can have arbitrary names, ie; "myalgo.py".

    Example:
        ENTRYPOINT ["python3", "myalgo.py"]
    """
    dockerfile_path = f"{dockerfile_dir}/Dockerfile"

    with open(dockerfile_path, "r") as file:
        dockerfile = file.read()
        for line in dockerfile.split("\n"):
            if line.startswith("ENTRYPOINT"):
                return json.loads(line[len("ENTRYPOINT"):])

    raise Exception("Invalid Dockerfile: Cannot find ENTRYPOINT")


def _get_args(ctx: Context, is_testtuple_eval: bool) -> List[str]:

    task = ctx.task
    task_category = ctx.task_category
    task_data = ctx.task_data

    in_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.InModels)
    out_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.OutModels)
    openers_dir = os.path.join(SANDBOX_DIR, TaskDirName.Openers)
    datasamples_dir = os.path.join(SANDBOX_DIR, TaskDirName.Datasamples)
    perf_path = os.path.join(SANDBOX_DIR, TaskDirName.Perf, Filenames.Performance)
    pred_path = os.path.join(SANDBOX_DIR, TaskDirName.Pred, Filenames.Predictions)

    if is_testtuple_eval:
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
            command += [os.path.join(in_models_dir, model["key"]) for model in ctx.in_models]

        if rank:
            command += ["--rank", rank]

        command += ["--opener-path", os.path.join(openers_dir, task_data["data_manager_key"], Filenames.Opener)]
        command += ["--data-sample-paths"] + [
            os.path.join(datasamples_dir, key) for key in task_data["data_sample_keys"]
        ]
        command += ["--output-model-path", os.path.join(out_models_dir, Filenames.OutModel)]

    elif task_category == computetask_pb2.TASK_COMPOSITE:

        for input_model in ctx.in_models:
            cat = model_pb2.ModelCategory.Value(input_model["category"])
            if cat == model_pb2.MODEL_HEAD:
                command += ["--input-head-model-filename", os.path.join(in_models_dir, input_model["key"])]
            elif cat == model_pb2.MODEL_SIMPLE:
                command += ["--input-trunk-model-filename", os.path.join(in_models_dir, input_model["key"])]

        if rank:
            command += ["--rank", rank]

        command += ["--opener-path", os.path.join(openers_dir, task_data["data_manager_key"], Filenames.Opener)]
        command += ["--data-sample-paths"] + [
            os.path.join(datasamples_dir, key) for key in task_data["data_sample_keys"]
        ]
        command += ["--output-models-path", out_models_dir]
        command += ["--output-head-model-filename", Filenames.OutHeadModel]
        command += ["--output-trunk-model-filename", Filenames.OutTrunkModel]

    elif task_category == computetask_pb2.TASK_AGGREGATE:

        if ctx.in_models:
            command += [os.path.join(in_models_dir, model["key"]) for model in ctx.in_models]

        if rank:
            command += ["--rank", rank]

        command += ["--output-model-path", os.path.join(out_models_dir, Filenames.OutModel)]

    elif task_category == computetask_pb2.TASK_TEST:

        for input_model in ctx.in_models:
            model_cat = model_pb2.ModelCategory.Value(input_model["category"])
            algo_cat = algo_pb2.AlgoCategory.Value(ctx.algo["category"])
            if model_cat == model_pb2.MODEL_HEAD:
                command += ["--input-head-model-filename", os.path.join(in_models_dir, input_model["key"])]
            elif model_cat == model_pb2.MODEL_SIMPLE and algo_cat == algo_pb2.ALGO_COMPOSITE:
                command += ["--input-trunk-model-filename", os.path.join(in_models_dir, input_model["key"])]
            else:
                command += [os.path.join(in_models_dir, input_model["key"])]

        command += ["--opener-path", os.path.join(openers_dir, task_data["data_manager_key"], Filenames.Opener)]
        command += ["--data-sample-paths"] + [
            os.path.join(datasamples_dir, key) for key in task_data["data_sample_keys"]
        ]
        command += ["--output-predictions-path", pred_path]

    return command
