import json
import os
import tarfile
import tempfile

import boto3
import structlog

from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import TaskDirName
from substrapp.utils import do_not_raise
from substrapp.utils import timeit

TAG_VALUE_FOR_TRANSFER_BUCKET = "transferBucket"
TRANSFER_BUCKET_TESTTUPLE_TAG = "TESTTUPLE_TAG"

ACCESS_KEY = os.getenv("BUCKET_TRANSFER_ID")
SECRET_KEY = os.getenv("BUCKET_TRANSFER_SECRET")
BUCKET_NAME = os.getenv("BUCKET_TRANSFER_NAME")
S3_PREFIX = os.getenv("BUCKET_TRANSFER_PREFIX")
S3_REGION_NAME = os.getenv("BUCKET_TRANSFER_REGION", "eu-west-1")

logger = structlog.get_logger(__name__)


@do_not_raise
@timeit
def transfer_to_bucket(ctx: Context) -> None:
    if not ACCESS_KEY or not SECRET_KEY or not BUCKET_NAME:
        redacted_secret_key = "*" * len(SECRET_KEY) if SECRET_KEY else None
        logger.error(
            "S3 settings for bucket transfer are not set",
            ACCESS_KEY=ACCESS_KEY,
            SECRET_KEY=redacted_secret_key,
            BUCKET_NAME=BUCKET_NAME,
        )
        return

    paths = [
        (os.path.join(ctx.directories.task_dir, TaskDirName.Pred), TaskDirName.Pred),
        (os.path.join(ctx.directories.task_dir, TaskDirName.Perf), TaskDirName.Perf),
        (os.path.join(ctx.directories.task_dir, TaskDirName.Export), TaskDirName.Export),
    ]

    export_metadata = {
        "task": ctx.task,
        "compute_plan": ctx.compute_plan,
        "dataset_name": ctx.data_manager["name"],
        "metrics": ctx.metrics,
    }

    # Here we take only the basename of the string provided.
    # This avoids a potential path traversal attack in the final archive
    # or uploading in an unexpected bucket.
    safe_compute_plan_tag = None
    if ctx.compute_plan_tag:
        safe_compute_plan_tag = os.path.basename(ctx.compute_plan_tag)

    with tempfile.TemporaryDirectory() as tmpdir:
        tar_name = f"{ctx.task_rank}_{ctx.compute_plan_key}_{ctx.task['key']}"
        if safe_compute_plan_tag:
            tar_name = f"{safe_compute_plan_tag}_" + tar_name

        tar_filename = tar_name + ".tar.gz"
        tar_path = os.path.join(tmpdir, tar_filename)
        logger.debug("writing archive", directory=tmpdir, name=tar_filename)

        metadata_filename = "metadata.json"
        metadata_filepath = os.path.join(tmpdir, metadata_filename)
        with open(metadata_filepath, "w") as metadata_file:
            json.dump(export_metadata, metadata_file)

        paths.append((metadata_filepath, metadata_filename))

        with tarfile.open(tar_path, "x:gz") as tar:
            for dir_path in paths:
                src, arcname = dir_path
                # We add the folders from the task but rename them to make the directory
                # structure in the archive simpler
                tar.add(src, arcname=os.path.join(tar_name, arcname))

        # Archive structure should look like this:
        # archive_filename/
        # ├─ export/
        # │  ├─ hyperparameters.json
        # │  ├─ model
        # ├─ perf/
        # │  ├─ uuid1-perf.json
        # │  ├─ uuid2-perf.json
        # ├─ pred/
        # │  ├─ pred.json
        # ├─ metadata.json

        s3 = boto3.client(
            "s3",
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=S3_REGION_NAME,
        )

        s3.upload_file(tar_path, BUCKET_NAME, f"{S3_PREFIX}/{tar_filename}" if S3_PREFIX else tar_filename)
