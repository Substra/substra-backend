import os
import structlog
import boto3
import tarfile
import tempfile
from substrapp.utils import timeit
from substrapp.utils import do_not_raise
from substrapp.compute_tasks.context import Context
from substrapp.compute_tasks.directories import TaskDirName


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
        logger.error("S3 settings for bucket transfer are not set",
                     ACCESS_KEY=ACCESS_KEY,
                     SECRET_KEY=redacted_secret_key,
                     BUCKET_NAME=BUCKET_NAME,
                     )
        return

    paths = [
        os.path.join(ctx.directories.task_dir, TaskDirName.Pred),
        os.path.join(ctx.directories.task_dir, TaskDirName.Perf),
        os.path.join(ctx.directories.task_dir, TaskDirName.Export),
    ]

    with tempfile.TemporaryDirectory(prefix="/tmp/") as tmpdir:

        tar_name = f"{ctx.compute_plan_key}-{ctx.task['key']}.tar.gz"
        tar_path = os.path.join(tmpdir, tar_name)

        with tarfile.open(tar_path, "x:gz") as tar:
            for dir_path in paths:
                tar.add(dir_path)

        s3 = boto3.client(
            "s3",
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=S3_REGION_NAME,
        )

        s3.upload_file(
            tar_path, BUCKET_NAME, f"{S3_PREFIX}/{tar_name}" if S3_PREFIX else tar_name
        )
