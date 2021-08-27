import os
import json
from typing import Tuple, List
from substrapp.ledger.api import get_object_from_ledger
from substrapp.compute_tasks.categories import (
    TASK_CATEGORY_TRAINTUPLE,
    TASK_CATEGORY_AGGREGATETUPLE,
    TASK_CATEGORY_COMPOSITETRAINTUPLE,
    TASK_CATEGORY_TESTTUPLE,
)
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import TaskDirName, SANDBOX_DIR


class Filenames:
    OutModel = "out-model"
    OutHeadModel = "out-head-model"
    OutTrunkModel = "out-trunk-model"
    Opener = "__init__.py"
    Predictions = "pred.json"
    Performance = "perf.json"


TASK_COMMANDS = {
    TASK_CATEGORY_TRAINTUPLE: "train",
    TASK_CATEGORY_TESTTUPLE: "predict",
    TASK_CATEGORY_COMPOSITETRAINTUPLE: "train",
    TASK_CATEGORY_AGGREGATETUPLE: "aggregate",
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

    channel_name = ctx.channel_name
    task = ctx.task
    task_category = ctx.task_category

    in_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.InModels)
    out_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.OutModels)
    openers_dir = os.path.join(SANDBOX_DIR, TaskDirName.Openers)
    datasamples_dir = os.path.join(SANDBOX_DIR, TaskDirName.Datasamples)
    perf_path = os.path.join(SANDBOX_DIR, TaskDirName.Perf, Filenames.Performance)
    pred_path = os.path.join(SANDBOX_DIR, TaskDirName.Pred, Filenames.Predictions)

    if is_testtuple_eval:
        command = ["--input-predictions-path", pred_path]
        command += ["--opener-path", os.path.join(openers_dir, task["dataset"]["key"], Filenames.Opener)]
        command += ["--data-sample-paths"] + [
            os.path.join(datasamples_dir, key) for key in task["dataset"]["data_sample_keys"]
        ]
        command += ["--output-perf-path", perf_path]
        return command

    compute_plan_key = None
    if "compute_plan_key" in task and task["compute_plan_key"]:
        compute_plan_key = task["compute_plan_key"]
    rank = str(task["rank"]) if compute_plan_key else None

    command = [TASK_COMMANDS[task_category]]

    if task_category == TASK_CATEGORY_TRAINTUPLE:

        if task["in_models"]:
            # TODO orchestrator
            # This should be in_model_keys = [model['key'] for model in subtuple["in_models"]]
            # but there's a bug in the chaincode... this will be fixed with the orchestrator
            in_model_keys = [
                get_traintuple_out_model_key(channel_name, model["traintuple_key"]) for model in task["in_models"]
            ]
            command += [os.path.join(in_models_dir, key) for key in in_model_keys]

        if rank:
            command += ["--rank", rank]
        command += ["--opener-path", os.path.join(openers_dir, task["dataset"]["key"], Filenames.Opener)]
        command += ["--data-sample-paths"] + [
            os.path.join(datasamples_dir, key) for key in task["dataset"]["data_sample_keys"]
        ]
        command += ["--output-model-path", os.path.join(out_models_dir, Filenames.OutModel)]

    elif task_category == TASK_CATEGORY_TESTTUPLE:

        if task["traintuple_type"] == TASK_CATEGORY_COMPOSITETRAINTUPLE:
            head_model_key, trunk_model_key = get_composite_traintuple_out_model_keys(
                channel_name, task["traintuple_key"]
            )
            command += ["--input-head-model-filename", os.path.join(in_models_dir, head_model_key)]
            command += ["--input-trunk-model-filename", os.path.join(in_models_dir, trunk_model_key)]

        elif task["traintuple_type"] == TASK_CATEGORY_TRAINTUPLE:
            in_model_key = get_traintuple_out_model_key(channel_name, task["traintuple_key"])
            command += [os.path.join(in_models_dir, in_model_key)]

        elif task["traintuple_type"] == TASK_CATEGORY_AGGREGATETUPLE:
            in_model_key = get_aggregatetuple_out_model_key(channel_name, task["traintuple_key"])
            command += [os.path.join(in_models_dir, in_model_key)]

        else:
            raise NotImplementedError

        command += ["--opener-path", os.path.join(openers_dir, task["dataset"]["key"], Filenames.Opener)]
        command += ["--data-sample-paths"] + [
            os.path.join(datasamples_dir, key) for key in task["dataset"]["data_sample_keys"]
        ]
        command += ["--output-predictions-path", pred_path]

    elif task_category == TASK_CATEGORY_COMPOSITETRAINTUPLE:

        if task["in_head_model"] and task["in_trunk_model"]:
            command += ["--input-head-model-filename", os.path.join(in_models_dir, task["in_head_model"]["key"])]
            command += ["--input-trunk-model-filename", os.path.join(in_models_dir, task["in_trunk_model"]["key"])]

        if rank:
            command += ["--rank", rank]

        command += ["--opener-path", os.path.join(openers_dir, task["dataset"]["key"], Filenames.Opener)]
        command += ["--data-sample-paths"] + [
            os.path.join(datasamples_dir, key) for key in task["dataset"]["data_sample_keys"]
        ]
        command += ["--output-models-path", out_models_dir]
        command += ["--output-head-model-filename", Filenames.OutHeadModel]
        command += ["--output-trunk-model-filename", Filenames.OutTrunkModel]

    elif task_category == TASK_CATEGORY_AGGREGATETUPLE:

        if task["in_models"]:
            in_model_keys = [model["key"] for model in task["in_models"]]
            command += [os.path.join(in_models_dir, key) for key in in_model_keys]

        if rank:
            command += ["--rank", rank]

        command += ["--output-model-path", os.path.join(out_models_dir, Filenames.OutModel)]

    return command


def get_traintuple_out_model(channel_name: str, task_key: str) -> str:
    metadata = get_object_from_ledger(channel_name, task_key, "queryTraintuple")
    return metadata["out_model"]


def get_traintuple_out_model_key(channel_name: str, task_key: str) -> str:
    model = get_traintuple_out_model(channel_name, task_key)
    return model["key"]


def get_aggregatetuple_out_model(channel_name: str, task_key: str) -> str:
    metadata = get_object_from_ledger(channel_name, task_key, "queryAggregatetuple")
    return metadata["out_model"]


def get_aggregatetuple_out_model_key(channel_name: str, task_key: str) -> str:
    model = get_aggregatetuple_out_model(channel_name, task_key)
    return model["key"]


def get_composite_traintuple_out_models(channel_name: str, task_key: str) -> Tuple[str, str]:
    metadata = get_object_from_ledger(channel_name, task_key, "queryCompositeTraintuple")
    return (
        metadata["out_head_model"]["out_model"],
        metadata["out_trunk_model"]["out_model"],
    )


def get_composite_traintuple_out_model_keys(channel_name: str, task_key: str) -> Tuple[str, str]:
    models = get_composite_traintuple_out_models(channel_name, task_key)
    return [models[0]["key"], models[1]["key"]]
