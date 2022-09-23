import json
import os

import structlog

import orchestrator
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.context import TaskResource
from substrapp.compute_tasks.directories import SANDBOX_DIR
from substrapp.compute_tasks.directories import Directories
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.models.image_entrypoint import ImageEntrypoint

logger = structlog.get_logger(__name__)

# This constant is shared with substra-tools.
# It will disappear once the inputs/outputs are exposed by the orchestrator.
TASK_IO_CHAINKEYS = "chainkeys"


class Filenames:
    Opener = "__init__.py"
    CliArgs = "arguments.txt"


def get_exec_command(ctx: Context) -> list[str]:
    entrypoint = ImageEntrypoint.objects.get(algo_checksum=ctx.algo.algorithm.checksum)

    command = entrypoint.entrypoint_json

    if command[0].startswith("python"):
        command.insert(1, "-u")  # unbuffered. Allows streaming the logs in real-time.

    # Pass the command line arguments via a file
    command.append("@" + os.path.join(SANDBOX_DIR, TaskDirName.CliArgs, Filenames.CliArgs))

    return command


def get_exec_command_args(ctx: Context) -> list[str]:
    """Return the substra-tools command line arguments"""
    task = ctx.task
    task_category = ctx.task.category

    in_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.InModels)
    openers_dir = os.path.join(SANDBOX_DIR, TaskDirName.Openers)
    datasamples_dir = os.path.join(SANDBOX_DIR, TaskDirName.Datasamples)
    chainkeys_folder = os.path.join(SANDBOX_DIR, TaskDirName.Chainkeys)

    inputs = []
    outputs = []

    # TODO: refactor path handling in context to iterate over all inputs at once
    inputs.extend(
        [
            TaskResource(
                id=input.identifier,
                value=os.path.join(in_models_dir, input.model.key),
                multiple=ctx.algo.inputs[input.identifier].multiple,
            )
            for input in ctx.input_assets
            if input.kind == orchestrator.AssetKind.ASSET_MODEL
        ]
    )
    inputs.extend(
        [
            TaskResource(
                id=input.identifier,
                value=os.path.join(openers_dir, input.data_manager.key, Filenames.Opener),
                multiple=ctx.algo.inputs[input.identifier].multiple,
            )
            for input in ctx.input_assets
            if input.kind == orchestrator.AssetKind.ASSET_DATA_MANAGER
        ]
    )
    inputs.extend(
        [
            TaskResource(
                id=input.identifier,
                value=os.path.join(datasamples_dir, input.data_sample.key),
                multiple=ctx.algo.inputs[input.identifier].multiple,
            )
            for input in ctx.input_assets
            if input.kind == orchestrator.AssetKind.ASSET_DATA_SAMPLE
        ]
    )

    for output in ctx.outputs:
        outputs.append(TaskResource(id=output.identifier, value=os.path.join(SANDBOX_DIR, output.rel_path)))

    args = []

    rank = str(task.rank)
    if rank and task_category != orchestrator.ComputeTaskCategory.TASK_PREDICT:
        args += ["--rank", rank]
    if ctx.has_chainkeys:
        inputs.append(TaskResource(id=TASK_IO_CHAINKEYS, value=chainkeys_folder))

    args += ["--inputs", json.dumps(inputs)]
    args += ["--outputs", json.dumps(outputs)]

    logger.debug("Generated substra-tools arguments", args=args)

    return args


def write_command_args_file(dirs: Directories, command_args: list[str]) -> None:
    """Write the substra-tools command line arguments to a file.

    The format uses one line per argument. See
    https://docs.python.org/3/library/argparse.html#fromfile-prefix-chars
    """
    path = os.path.join(dirs.task_dir, TaskDirName.CliArgs, Filenames.CliArgs)

    with open(path, "w") as f:
        for item in command_args:
            f.write(item + "\n")
