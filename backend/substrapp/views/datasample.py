import os
import shutil
import tarfile
import tempfile
import zipfile
from tarfile import TarFile
from typing import BinaryIO
from typing import List
from typing import Tuple
from typing import Union

import structlog
from django.conf import settings
from django.core.files import File
from rest_framework import mixins
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import GenericViewSet

from libs.pagination import DefaultPageNumberPagination
from libs.pagination import PaginationMixin
from localrep.errors import AlreadyExistsError
from localrep.models import DataManager as DataManagerRep
from localrep.models import DataSample as DataSampleRep
from localrep.serializers import DataSampleSerializer as DataSampleRepSerializer
from substrapp import exceptions
from substrapp.exceptions import ServerMediasNoSubdirError
from substrapp.models import DataManager
from substrapp.models import DataSample
from substrapp.orchestrator import get_orchestrator_client
from substrapp.serializers import DataSampleSerializer
from substrapp.serializers import OrchestratorDataSampleSerializer
from substrapp.serializers import OrchestratorDataSampleUpdateSerializer
from substrapp.utils import ZipFile
from substrapp.utils import get_dir_hash
from substrapp.utils import raise_if_path_traversal
from substrapp.views.utils import ApiResponse
from substrapp.views.utils import get_channel_name

logger = structlog.get_logger(__name__)


class DataSampleViewSet(mixins.CreateModelMixin, PaginationMixin, GenericViewSet):
    queryset = DataSample.objects.all()
    serializer_class = DataSampleSerializer
    pagination_class = DefaultPageNumberPagination

    def create(self, request, *args, **kwargs):
        try:
            data = self._create(request)
        # FIXME: `serializers.ValidationError` are automatically handled by DRF and should
        #  not be caught to return a response. The following code only exists to preserve
        #  a previously established API contract.
        except serializers.ValidationError as e:
            return ApiResponse({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        headers = self.get_success_headers(data)
        return ApiResponse(data, status=status.HTTP_201_CREATED, headers=headers)

    def _create(self, request):
        data_manager_keys = request.data.get("data_manager_keys") or []
        self.check_datamanagers(data_manager_keys)

        # incrementally save in db
        instances = []
        for file_data in self._get_files(request):
            instances.append(self._db_create(file_data))

        # serialized data for orchestrator db
        orchestrator_serializer = OrchestratorDataSampleSerializer(
            data={
                "test_only": request.data.get("test_only", False),
                "data_manager_keys": request.data.get("data_manager_keys") or [],
                "instances": instances,
            },
            context={"request": request},
        )

        if not orchestrator_serializer.is_valid():
            for instance in instances:
                instance.delete()  # warning: post delete signals are not executed by django rollback
            raise ValidationError(orchestrator_serializer.errors)

        # create on orchestrator db
        try:
            orchestrator_serializer.create(get_channel_name(request), orchestrator_serializer.validated_data)
        except Exception:
            for instance in instances:
                instance.delete()  # warning: post delete signals are not executed by django rollback
            raise

        # Save in local db to ensure consistency
        self._localrep_create(request, instances)
        return [self.get_serializer(instance).data for instance in instances]

    def _localrep_create(self, request, instances):
        for instance in instances:
            with get_orchestrator_client(get_channel_name(request)) as client:
                localrep_data = client.query_datasample(str(instance.key))
            localrep_data["channel"] = get_channel_name(request)
            localrep_serializer = DataSampleRepSerializer(data=localrep_data)
            try:
                localrep_serializer.save_if_not_exists()
            except AlreadyExistsError:
                pass
            except Exception:
                for instance in instances:
                    instance.delete()  # warning: post delete signals are not executed by django rollback
                raise

    def _db_create(self, data):
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # FIXME: This try/except block is only here to ensure
        #  a previously established API contract is respected.
        try:
            return serializer.save()
        except Exception as e:
            raise exceptions.BadRequestError(str(e))

    @staticmethod
    def check_datamanagers(data_manager_keys):
        if not data_manager_keys:
            raise exceptions.BadRequestError("missing or empty field 'data_manager_keys'")
        datamanager_count = DataManager.objects.filter(key__in=data_manager_keys).count()
        if datamanager_count != len(data_manager_keys):
            raise exceptions.BadRequestError(
                "One or more datamanager keys provided do not exist in local database. "
                f"Please create them before. DataManager keys: {data_manager_keys}"
            )

    def _get_files(self, request):
        return (
            self._get_files_from_http_upload(request) if request.FILES else self._get_files_from_servermedias(request)
        )

    @staticmethod
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
                    logger.error(e)
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

    @staticmethod
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

        for path in paths:
            _validate_servermedias_path(path)

            checksum = get_dir_hash(path)

            if settings.ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS:  # save path
                yield {"path": path, "checksum": checksum}

            else:  # upload to MinIO
                with tempfile.TemporaryDirectory() as archive_tmp_path:
                    archive = shutil.make_archive(archive_tmp_path, "tar", root_dir=path)
                yield {"file": File(open(archive, "rb")), "checksum": checksum}

    def list(self, request, *args, **kwargs):
        with get_orchestrator_client(get_channel_name(request)) as client:
            data = client.query_datasamples()

        return self.paginate_response(data)

    @action(methods=["post"], detail=False)
    def bulk_update(self, request):
        # serialized data for orchestrator db
        orchestrator_serializer = OrchestratorDataSampleUpdateSerializer(
            data=dict(request.data), context={"request": request}
        )
        orchestrator_serializer.is_valid(raise_exception=True)

        # create on orchestrator db
        data = orchestrator_serializer.create(get_channel_name(request), orchestrator_serializer.validated_data)

        # Update relations directly in local db to ensure consistency
        data_sample_keys = [str(key) for key in orchestrator_serializer.validated_data.get("data_sample_keys")]
        data_manager_keys = [str(key) for key in orchestrator_serializer.validated_data.get("data_manager_keys")]
        data_managers = DataManagerRep.objects.filter(key__in=data_manager_keys)
        data_samples = DataSampleRep.objects.filter(key__in=data_sample_keys)
        for data_sample in data_samples:
            # WARNING: bulk update is only for adding new links, not for removing ones
            data_sample.data_managers.add(*data_managers)
            data_sample.save()

        return ApiResponse(data, status=status.HTTP_200_OK)


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


def _get_archive_and_files(f: BinaryIO) -> Tuple[Union[ZipFile, TarFile], List[str]]:
    if zipfile.is_zipfile(f):
        archive = zipfile.ZipFile(file=f)
        return archive, archive.namelist()
    f.seek(0)
    try:
        archive = tarfile.open(fileobj=f)
        return archive, archive.getnames()
    except tarfile.TarError:
        raise serializers.ValidationError("Archive must be zip or tar")
