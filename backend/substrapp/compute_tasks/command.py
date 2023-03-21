import json
import os
from typing import cast

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
    entrypoint = ImageEntrypoint.objects.get(function_checksum=ctx.function.function_address.checksum)

    command = entrypoint.entrypoint_json

    if command[0].startswith("python"):
        command.insert(1, "-u")  # unbuffered. Allows streaming the logs in real-time.

    # Pass the command line arguments via a file
    command.append("@" + os.path.join(SANDBOX_DIR, TaskDirName.CliArgs, Filenames.CliArgs))

    return command


def get_exec_command_args(ctx: Context) -> list[str]:
    """Return the substra-tools command line arguments"""
    task = ctx.task

    in_models_dir = os.path.join(SANDBOX_DIR, TaskDirName.InModels)
    openers_dir = os.path.join(SANDBOX_DIR, TaskDirName.Openers)
    datasamples_dir = os.path.join(SANDBOX_DIR, TaskDirName.Datasamples)
    chainkeys_folder = os.path.join(SANDBOX_DIR, TaskDirName.Chainkeys)

    inputs = []
    outputs = []

    for input_asset in ctx.input_assets:
        identifier = input_asset.identifier
        multiple = ctx.function.inputs[input_asset.identifier].multiple

        value = None
        # `cast()` are needed as we use `Optional`
        if input_asset.kind == orchestrator.AssetKind.ASSET_MODEL:
            model = cast(orchestrator.resources.Model, input_asset.model)
            value = os.path.join(in_models_dir, model.key)
        elif input_asset.kind == orchestrator.AssetKind.ASSET_DATA_MANAGER:
            data_manager = cast(orchestrator.resources.DataManager, input_asset.data_manager)
            value = os.path.join(openers_dir, data_manager.key, Filenames.Opener)
        elif input_asset.kind == orchestrator.AssetKind.ASSET_DATA_SAMPLE:
            data_sample = cast(orchestrator.resources.DataSample, input_asset.data_sample)
            value = os.path.join(datasamples_dir, data_sample.key)

        if value is not None:
            inputs.append(
                TaskResource(
                    id=identifier,
                    value=value,
                    multiple=multiple,
                )
            )

    for output in ctx.outputs:
        outputs.append(TaskResource(id=output.identifier, value=os.path.join(SANDBOX_DIR, output.rel_path)))

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
