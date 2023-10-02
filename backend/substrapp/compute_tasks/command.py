import json
import os

import structlog

import orchestrator
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.context import OutputResource
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
    entrypoint = ImageEntrypoint.objects.get(archive_checksum=ctx.function.archive_address.checksum)

    command = entrypoint.entrypoint_json

    if command[0].startswith("python"):
        command.insert(1, "-u")  # unbuffered. Allows streaming the logs in real-time.

    # Pass the command line arguments via a file
    command.append("@" + os.path.join(SANDBOX_DIR, TaskDirName.CliArgs, Filenames.CliArgs))

    return command


def _get_input_tasks(
    input_assets: list[orchestrator.ComputeTaskInputAsset], function: orchestrator.Function
) -> list[TaskResource]:
    """Return a list of `TaskResource` for all inputs"""
    in_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.InModels)
    openers_dir = os.path.join(SANDBOX_DIR, TaskDirName.Openers)
    datasamples_dir = os.path.join(SANDBOX_DIR, TaskDirName.Datasamples)

    inputs = []
    for input_asset in input_assets:
        identifier = input_asset.identifier
        multiple = function.inputs[input_asset.identifier].multiple

        value = None
        if input_asset.kind == orchestrator.AssetKind.ASSET_MODEL:
            model = input_asset.model
            if model is None:
                raise ValueError(f"model cannot be None when {input_asset.kind=}")
            value = os.path.join(in_models_dir, model.key)
        elif input_asset.kind == orchestrator.AssetKind.ASSET_DATA_MANAGER:
            data_manager = input_asset.data_manager
            if data_manager is None:
                raise ValueError(f"data_manager cannot be None when {input_asset.kind=}")
            value = os.path.join(openers_dir, data_manager.key, Filenames.Opener)
        elif input_asset.kind == orchestrator.AssetKind.ASSET_DATA_SAMPLE:
            data_sample = input_asset.data_sample
            if data_sample is None:
                raise ValueError(f"data_sample cannot be None when {input_asset.kind=}")
            value = os.path.join(datasamples_dir, data_sample.key)

        if value is not None:
            inputs.append(
                TaskResource(
                    id=identifier,
                    value=value,
                    multiple=multiple,
                )
            )

    return inputs


def _get_output_tasks(outputs: list[OutputResource]) -> list[TaskResource]:
    """Return a list of `TaskResource` for all outputs"""
    return [TaskResource(id=output.identifier, value=os.path.join(SANDBOX_DIR, output.rel_path)) for output in outputs]


def get_exec_command_args(ctx: Context) -> list[str]:
    """Return the substra-tools command line arguments"""
    task = ctx.task

    chainkeys_folder = os.path.join(SANDBOX_DIR, TaskDirName.Chainkeys)

    inputs = _get_input_tasks(ctx.input_assets, ctx.function)
    outputs = _get_output_tasks(ctx.outputs)

    task_properties = {"rank": task.rank}
    args = ["--task-properties", json.dumps(task_properties)]

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
