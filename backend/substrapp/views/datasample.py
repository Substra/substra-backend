import logging
import os
import shutil
import uuid

from os.path import normpath
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from substrapp.exceptions import ServerMediasPathError, ServerMediasNoSubdirError

from substrapp.models import DataSample, DataManager
from substrapp.serializers import (DataSampleSerializer,
                                   OrchestratorDataSampleSerializer,
                                   OrchestratorDataSampleUpdateSerializer)
from substrapp.utils import store_datasamples_archive, get_dir_hash
from libs.pagination import DefaultPageNumberPagination, PaginationMixin
from substrapp.views.utils import ValidationExceptionError, get_channel_name

from substrapp.orchestrator.api import get_orchestrator_client
from substrapp.orchestrator.error import OrcError

logger = logging.getLogger(__name__)


class DataSampleViewSet(mixins.CreateModelMixin, PaginationMixin, GenericViewSet):
    queryset = DataSample.objects.all()
    serializer_class = DataSampleSerializer
    pagination_class = DefaultPageNumberPagination

    def create(self, request, *args, **kwargs):

        try:
            data = self._create(request)
        except ValidationExceptionError as e:
            return Response({'message': e.data, 'key': e.key}, status=e.st)
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            headers = self.get_success_headers(data)
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def _create(self, request):
        paths_to_remove = []
        data_manager_keys = request.data.get("data_manager_keys") or []
        self.check_datamanagers(data_manager_keys)

        try:
            # incrementally save in db
            instances = []
            for file_data in self._get_files(request, paths_to_remove):
                instances.append(self._db_create(data=file_data))

            # serialized data for orchestrator db
            orchestrator_serializer = OrchestratorDataSampleSerializer(
                data={
                    'test_only': request.data.get('test_only', False),
                    'data_manager_keys': request.data.get('data_manager_keys') or [],
                    'instances': instances
                },
                context={
                    'request': request
                }
            )

            if not orchestrator_serializer.is_valid():
                for instance in instances:
                    instance.delete()
                raise ValidationError(orchestrator_serializer.errors)

            # create on orchestrator db
            try:
                orchestrator_result = orchestrator_serializer.create(
                    get_channel_name(request),
                    orchestrator_serializer.validated_data
                )
            except Exception:
                for instance in instances:
                    instance.delete()
                raise

            data = []
            for instance in instances:
                serializer = self.get_serializer(instance)
                if (
                    "key" in orchestrator_result and
                    orchestrator_result["validated"] and
                    serializer.data["key"] in orchestrator_result["key"]
                ):
                    serializer.data["validated"] = True
                data.append(serializer.data)
            return data

        finally:
            for gpath in paths_to_remove:
                shutil.rmtree(gpath, ignore_errors=True)

    def _db_create(self, data):
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    @staticmethod
    def check_datamanagers(data_manager_keys):
        if not data_manager_keys:
            raise Exception("missing or empty field 'data_manager_keys'")
        datamanager_count = DataManager.objects.filter(key__in=data_manager_keys).count()
        if datamanager_count != len(data_manager_keys):
            raise Exception(
                "One or more datamanager keys provided do not exist in local database. "
                f"Please create them before. DataManager keys: {data_manager_keys}"
            )

    @staticmethod
    def _get_files(request, paths_to_remove: list):
        """
        Preprocess files on view side (instead of serializer)
        is more handy to deal with inputs heterogeneity
        """
        # mode 1: files uploaded via http
        if len(request.FILES) > 0:
            for f in request.FILES.values():
                key = uuid.uuid4()
                checksum, datasamples_path_from_file = store_datasamples_archive(f)  # can raise
                paths_to_remove.append(datasamples_path_from_file)
                yield {"key": key, "path": datasamples_path_from_file, "checksum": checksum}
            return

        # mode 2: files present on file system
        path = request.data.get("path")
        paths = request.data.get("paths") or []
        if path and paths:
            raise Exception("Cannot use path and paths together.")
        if path is not None:
            paths = [path]

        if request.data.get("multiple") in (True, "true"):
            paths = get_subpaths(paths, raise_no_subdir=True)

        for path in paths:
            validate_servermedias_path(path)

            key = uuid.uuid4()
            checksum = get_dir_hash(path)

            yield {"key": key, "path": normpath(path), "checksum": checksum}

    def list(self, request, *args, **kwargs):
        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                data = client.query_datasamples()
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return self.paginate_response(data)

    @action(methods=["post"], detail=False)
    def bulk_update(self, request):

        # serialized data for orchestrator db
        orchestrator_serializer = OrchestratorDataSampleUpdateSerializer(
            data=dict(request.data),
            context={
                'request': request
            }
        )
        orchestrator_serializer.is_valid(raise_exception=True)

        # create on orchestrator db
        try:
            data = orchestrator_serializer.create(
                get_channel_name(request),
                orchestrator_serializer.validated_data
            )
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)


def get_subpaths(paths, raise_no_subdir=False):
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


def validate_servermedias_path(path):
    if not os.path.exists(path):
        raise ServerMediasPathError(f"Invalid path, not found: {path}")
    if not os.path.isdir(path):
        raise ServerMediasPathError(f"Invalid path, not a directory: {path}")
    if not os.listdir(path):
        raise ServerMediasPathError(f"Invalid path, empty directory: {path}")
