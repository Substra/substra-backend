import json
import os

import structlog

import orchestrator
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.context import TaskResource
from substrapp.compute_tasks.directories import SANDBOX_DIR
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.models.image_entrypoint import ImageEntrypoint

logger = structlog.get_logger(__name__)

# These constants are shared with connect-tools.
# These constants will disappear once the inputs/outputs are exposed by the orchestrator.
TASK_IO_PREDICTIONS = "predictions"
TASK_IO_CHAINKEYS = "chainkeys"
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
    orchestrator.ComputeTaskCategory.TASK_TRAIN: "train",
    orchestrator.ComputeTaskCategory.TASK_PREDICT: "predict",
    orchestrator.ComputeTaskCategory.TASK_COMPOSITE: "train",
    orchestrator.ComputeTaskCategory.TASK_AGGREGATE: "aggregate",
}


def get_performance_filename(algo_key: str) -> str:
    """Builds the performance filename

    Args:
        algo_key: The key of the algo that produce this performance file.

    Returns:
        A string representation of the performance filename.
    """
    return "-".join([algo_key, Filenames.Performance])


def get_exec_command(ctx: Context) -> list[str]:
    entrypoint = ImageEntrypoint.objects.get(algo_checksum=ctx.algo.checksum)

    command = entrypoint.entrypoint_json

    if command[0].startswith("python"):
        command.insert(1, "-u")  # unbuffered. Allows streaming the logs in real-time.

    args = _get_args(ctx)

    return command + args


# TODO: '_get_args' is too complex, consider refactoring
def _get_args(ctx: Context) -> list[str]:  # noqa: C901
    task = ctx.task
    task_category = ctx.task.category

    in_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.InModels)
    out_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.OutModels)
    openers_dir = os.path.join(SANDBOX_DIR, TaskDirName.Openers)
    datasamples_dir = os.path.join(SANDBOX_DIR, TaskDirName.Datasamples)
    chainkeys_folder = os.path.join(SANDBOX_DIR, TaskDirName.Chainkeys)

    inputs = []
    outputs = []

    if task_category == orchestrator.ComputeTaskCategory.TASK_TEST:
        perf_path = os.path.join(SANDBOX_DIR, TaskDirName.Perf, get_performance_filename(ctx.algo.key))
        command = ["--input-predictions-path", os.path.join(in_models_dir, ctx.input_models[0].key)]
        command += ["--opener-path", os.path.join(openers_dir, ctx.data_manager.key, Filenames.Opener)]
        command += ["--data-sample-paths"] + [os.path.join(datasamples_dir, key) for key in ctx.data_sample_keys]
        command += ["--output-perf-path", perf_path]
        # use a fake TaskResource until everything is properly passed as a generic output
        ctx.set_outputs([TaskResource(id="performance", value=perf_path)])
        return command

    command = [TASK_COMMANDS[task_category]]

    # TODO: refactor path handling in context to iterate over all inputs at once
    inputs.extend(
        [
            TaskResource(id=input.identifier, value=os.path.join(in_models_dir, input.model.key))
            for input in ctx.input_assets
            if input.kind == orchestrator.AssetKind.ASSET_MODEL
        ]
    )
    inputs.extend(
        [
            TaskResource(id=input.identifier, value=os.path.join(openers_dir, input.data_manager.key, Filenames.Opener))
            for input in ctx.input_assets
            if input.kind == orchestrator.AssetKind.ASSET_DATA_MANAGER
        ]
    )
    inputs.extend(
        [
            TaskResource(id=input.identifier, value=os.path.join(datasamples_dir, input.data_sample.key))
            for input in ctx.input_assets
            if input.kind == orchestrator.AssetKind.ASSET_DATA_SAMPLE
        ]
    )

    if task_category == orchestrator.ComputeTaskCategory.TASK_TRAIN:
        outputs.append(TaskResource(id=TRAIN_IO_MODEL, value=os.path.join(out_models_dir, Filenames.OutModel)))

    elif task_category == orchestrator.ComputeTaskCategory.TASK_COMPOSITE:
        outputs.append(TaskResource(id=COMPOSITE_IO_LOCAL, value=os.path.join(out_models_dir, Filenames.OutHeadModel)))
        outputs.append(TaskResource(id=COMPOSITE_IO_SHARED, value=os.path.join(out_models_dir, Filenames.OutModel)))

    elif task_category == orchestrator.ComputeTaskCategory.TASK_AGGREGATE:
        outputs.append(TaskResource(id=TRAIN_IO_MODEL, value=os.path.join(out_models_dir, Filenames.OutModel)))

    elif task_category == orchestrator.ComputeTaskCategory.TASK_PREDICT:
        outputs.append(TaskResource(id=TASK_IO_PREDICTIONS, value=os.path.join(out_models_dir, Filenames.OutModel)))

    rank = str(task.rank)
    if rank and task_category != orchestrator.ComputeTaskCategory.TASK_PREDICT:
        command += ["--rank", rank]
    if ctx.has_chainkeys:
        inputs.append(TaskResource(id=TASK_IO_CHAINKEYS, value=chainkeys_folder))

    ctx.set_outputs(outputs)

    command += ["--inputs", f"'{json.dumps(inputs)}'"]
    command += ["--outputs", f"'{json.dumps(outputs)}'"]

    logger.debug("Generated task command", command=command)

    return command
