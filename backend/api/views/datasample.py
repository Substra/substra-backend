import os
import shutil
import tarfile
import tempfile
import zipfile
from tarfile import TarFile
from typing import BinaryIO
from typing import Union

import structlog
from django.conf import settings
from django.core.files import File
from django.db import models
from django_filters.rest_framework import BaseInFilter
from django_filters.rest_framework import CharFilter
from django_filters.rest_framework import DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework import mixins
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import GenericViewSet

from api.errors import AlreadyExistsError
from api.errors import BadRequestError
from api.models import DataManager
from api.models import DataSample
from api.serializers import DataSampleSerializer
from api.views.filters_utils import CharInFilter
from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from libs.pagination import DefaultPageNumberPagination
from substrapp.exceptions import ServerMediasNoSubdirError
from substrapp.models import DataManager as DataManagerFiles
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import DataSampleSerializer as DataSampleFilesSerializer
from substrapp.utils import ZipFile
from substrapp.utils import get_dir_hash
from substrapp.utils import raise_if_path_traversal

logger = structlog.get_logger(__name__)


def create(request, get_success_headers):
    try:
        data = _create(request)
    # FIXME: `serializers.ValidationError` are automatically handled by DRF and should
    #  not be caught to return a response. The following code only exists to preserve
    #  a previously established API contract.
    except serializers.ValidationError as e:
        return ApiResponse({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    headers = get_success_headers(data)
    return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)


def _create(request):
    """Create new datasamples.

    The workflow is composed of several steps:
    - Save files in local database to get the addresses.
    - Register assets in the orchestrator.
    - Save metadata in local database.
    """
    # Step1: save files in local database
    data_manager_keys = request.data.get("data_manager_keys") or []
    check_datamanagers(data_manager_keys)

    # incrementally save in db
    instances = {}
    for file_data in _get_files(request):
        instance = _db_create(file_data)
        instances[str(instance.key)] = instance

    # Step2: register asset in orchestrator
    try:
        orc_response = _register_in_orchestrator(request, instances.values())
    except Exception:
        for instance in instances.values():
            instance.delete()  # warning: post delete signals are not executed by django rollback
        raise

    # Step3: save metadata in local database
    return _api_create(request, instances, orc_response)


def _register_in_orchestrator(request, instances):
    """Register datasamples in orchestrator."""
    data_manager_keys = request.data.get("data_manager_keys") or []

    orc_ds = {
        "samples": [
            {
                "key": str(i.key),
                "data_manager_keys": [str(key) for key in data_manager_keys],
                "checksum": i.checksum,
            }
            for i in instances
        ]
    }
    with get_orchestrator_client(get_channel_name(request)) as client:
        return client.register_datasamples(orc_ds)


def _api_create(request, instances, orc_response):
    results = []
    for api_data in orc_response:
        api_data["channel"] = get_channel_name(request)
        api_serializer = DataSampleSerializer(data=api_data)
        try:
            api_serializer.save_if_not_exists()
        except AlreadyExistsError:
            data_sample = DataSample.objects.get(key=api_data["key"])
            data = DataSampleSerializer(data_sample).data
        except Exception:
            for instance in instances.values():
                instance.delete()  # warning: post delete signals are not executed by django rollback
            raise
        else:
            data = api_serializer.data
        result = DataSampleFilesSerializer(instances[data["key"]]).data
        result.update(data)
        results.append(result)
    return results


def _db_create(data):
    serializer = DataSampleFilesSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    # FIXME: This try/except block is only here to ensure
    #  a previously established API contract is respected.
    try:
        return serializer.save()
    except Exception as e:
        raise BadRequestError(str(e))


def check_datamanagers(data_manager_keys):
    if not data_manager_keys:
        raise BadRequestError("missing or empty field 'data_manager_keys'")
    datamanager_count = DataManagerFiles.objects.filter(key__in=data_manager_keys).count()
    if datamanager_count != len(data_manager_keys):
        raise BadRequestError(
            "One or more datamanager keys provided do not exist in local database. "
            f"Please create them before. DataManager keys: {data_manager_keys}"
        )


def _get_files(request):
    return _get_files_from_http_upload(request) if request.FILES else _get_files_from_servermedias(request)


def _get_files_from_http_upload(request):
    """
    Yield files uploaded via HTTP.

    The yielded dictionaries have a "file" key and a "checksum" key.
    """
    for f in request.FILES.values():
        try:
            f.seek(0)
        except Exception:
            raise serializers.ValidationError("Cannot handle this file object")
        else:
            archive = None

            try:
                archive = _get_archive(f)
            except Exception as e:
                logger.exception("failed to get archive", e=e)
                raise e
            else:
                with tempfile.TemporaryDirectory() as tmp_path:
                    archive.extractall(path=tmp_path)
                    checksum = get_dir_hash(tmp_path)
                f.seek(0)
                yield {"file": f, "checksum": checksum}
            finally:
                if archive:
                    archive.close()


def _get_files_from_servermedias(request):
    """
    Yield files from servermedias, based on the HTTP POST request's "path" and "paths" keys.

    The yielded dictionaries have a "path" key and a "checksum" key.
    """
    path = request.data.get("path")
    paths = request.data.get("paths") or []
    if path and paths:
        raise Exception("Cannot use path and paths together.")
    if path is not None:
        paths = [path]

    if request.data.get("multiple") in (True, "true"):
        paths = _get_servermedias_subpaths(paths, raise_no_subdir=True)

    logger.debug("Adding datasamples from servermedias", paths=paths)

    for path in paths:
        _validate_servermedias_path(path)

        # Here an issue could arise since we compute the checksum before archiving the data.
        # the data inside the directory could change before it is archived and uploaded to the storage backend (MinIO).
        checksum = get_dir_hash(path)

        if settings.ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS:  # save path
            yield {"path": path, "checksum": checksum}

        else:  # upload to MinIO
            with tempfile.TemporaryDirectory() as archive_tmp_path:
                archive = shutil.make_archive(archive_tmp_path, "tar", root_dir=path)
            yield {"file": File(open(archive, "rb")), "checksum": checksum}


def _get_servermedias_subpaths(paths, raise_no_subdir=False):
    """
    For each path, return path of first level subdirs.
    `raise_no_subdir` expect all paths to contain subdir(s).

    >>> get_subpaths(["/path/to/dir_a", "/path/to/dir_b"])
    [
        "/path/to/dir_a/subdir_a1",
        "/path/to/dir_a/subdir_a2",
        "/path/to/dir_b/subdir_b1",
        "/path/to/dir_b/subdir_b2",
    ]
    """
    subpaths = []
    for path in paths:
        _, subdirs, _ = next(os.walk(path))  # first level only
        for subdir in subdirs:
            subpaths.append(os.path.join(path, subdir))
        if raise_no_subdir and not subdirs:
            raise ServerMediasNoSubdirError(f"No directory found in: {path}")
    return subpaths


def _validate_servermedias_path(path):
    if os.path.islink(path):
        raise serializers.ValidationError(f"Invalid path, {path} should not use symlink")
    if not os.path.abspath(path).startswith(settings.SERVERMEDIAS_ROOT):
        raise serializers.ValidationError(f"Invalid path, should be a subdir of servermedias {path}")
    if not os.path.exists(path):
        raise serializers.ValidationError(f"Invalid path, not found: {path}")
    if not os.path.isdir(path):
        raise serializers.ValidationError(f"Invalid path, not a directory: {path}")
    if not os.listdir(path):
        raise serializers.ValidationError(f"Invalid path, empty directory: {path}")


def _get_archive(f: BinaryIO) -> Union[ZipFile, TarFile]:
    archive, files = _get_archive_and_files(f)
    if not len(files):
        raise serializers.ValidationError("Ensure your archive contains at least one file.")
    try:
        raise_if_path_traversal(files, "./")
    except Exception:
        raise serializers.ValidationError(
            "Ensure your archive does not contain traversal filenames (e.g. filename with `..` inside)"
        )

    return archive


def _get_archive_and_files(f: BinaryIO) -> tuple[Union[ZipFile, TarFile], list[str]]:
    if zipfile.is_zipfile(f):
        archive = zipfile.ZipFile(file=f)
        return archive, archive.namelist()
    f.seek(0)
    try:
        archive = tarfile.open(fileobj=f)
        return archive, archive.getnames()
    except tarfile.TarError:
        raise serializers.ValidationError("Archive must be zip or tar")


class DataSampleFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter()
    compute_plan_key = CharInFilter(
        field_name="data_managers__compute_tasks__compute_plan__key", distinct=True, label="compute_plan_key"
    )
    algo_key = CharFilter(field_name="compute_tasks__algo__key", distinct=True, label="algo_key")
    dataset_key = CharFilter(field_name="compute_tasks__data_manager__key", distinct=True, label="dataset_key")

    class Meta:
        model = DataSample
        fields = {
            "owner": ["exact"],
            "key": ["exact"],
        }
        filter_overrides = {
            models.CharField: {
                "filter_class": BaseInFilter,
                "extra": lambda f: {
                    "lookup_expr": "in",
                },
            },
            models.UUIDField: {
                "filter_class": BaseInFilter,
                "extra": lambda f: {
                    "lookup_expr": "in",
                },
            },
        }


class DataSampleViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = DataSampleSerializer
    filter_backends = (OrderingFilter, DjangoFilterBackend)
    ordering_fields = ["creation_date", "key", "owner"]
    ordering = ["creation_date", "key"]
    pagination_class = DefaultPageNumberPagination
    filterset_class = DataSampleFilter

    def get_queryset(self):
        return DataSample.objects.filter(channel=get_channel_name(self.request)).prefetch_related("data_managers")

    def create(self, request, *args, **kwargs):
        return create(request, lambda data: self.get_success_headers(data))

    @action(methods=["post"], detail=False)
    def bulk_update(self, request):
        # convert QueryDict request.data into dict
        # using QueryDict.getlist does not seem to work for all cases
        data_manager_keys = [str(key) for key in (dict(request.data).get("data_manager_keys") or [])]
        data_sample_keys = [str(key) for key in (dict(request.data).get("data_sample_keys") or [])]

        orc_ds = {
            "keys": data_sample_keys,
            "data_manager_keys": data_manager_keys,
        }
        with get_orchestrator_client(get_channel_name(request)) as client:
            data = client.update_datasample(orc_ds)

        # Update relations directly in local db to ensure consistency
        data_managers = DataManager.objects.filter(key__in=data_manager_keys)
        data_samples = DataSample.objects.filter(key__in=data_sample_keys)
        for data_sample in data_samples:
            # WARNING: bulk update is only for adding new links, not for removing ones
            data_sample.data_managers.add(*data_managers)
            data_sample.save()

        return ApiResponse(data, status=status.HTTP_200_OK)
