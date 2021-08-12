import logging
import os
import shutil
import uuid

from os.path import normpath
from django.conf import settings
from rest_framework import serializers, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from substrapp.exceptions import ServerMediasPathError, ServerMediasNoSubdirError

from substrapp.models import DataSample, DataManager
from substrapp.serializers import DataSampleSerializer, LedgerDataSampleSerializer, LedgerDataSampleUpdateSerializer
from substrapp.utils import store_datasamples_archive, get_dir_hash
from substrapp.views.utils import (
    LedgerExceptionError,
    ValidationExceptionError,
    get_success_create_code,
    get_channel_name,
)
from substrapp.ledger.api import query_ledger
from substrapp.ledger.exceptions import LedgerError, LedgerTimeoutError, LedgerConflictError
from libs.pagination import DefaultPageNumberPagination, PaginationMixin

logger = logging.getLogger(__name__)


class DataSampleViewSet(mixins.CreateModelMixin, PaginationMixin, GenericViewSet):
    queryset = DataSample.objects.all()
    serializer_class = DataSampleSerializer
    pagination_class = DefaultPageNumberPagination

    def create(self, request, *args, **kwargs):
        """Wrapper to handle exceptions and responses."""
        try:
            data = self._create(request)
        except ValidationExceptionError as e:
            return Response({"message": e.data}, status=e.st)
        except LedgerExceptionError as e:
            return Response({"message": e.data}, status=e.st)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            headers = self.get_success_headers(data)
            st = get_success_create_code()
            return Response(data, status=st, headers=headers)

    def _create(self, request):
        paths_to_remove = []
        data_manager_keys = request.data.get("data_manager_keys") or []
        self.check_datamanagers(data_manager_keys)

        try:
            # incrementally save in db
            instances = []
            for file_data in self._get_files(request, paths_to_remove):
                instances.append(self._db_create(data=file_data))

            # bulk save in ledger
            ledger_data = {
                "instances": instances,
                "data_manager_keys": data_manager_keys,
                "test_only": request.data.get("test_only", False),
            }
            try:
                ledger_result = self._ledger_create(ledger_data, get_channel_name(request))
            except LedgerTimeoutError as e:
                raise LedgerExceptionError("timeout", e.status)
            except LedgerConflictError as e:
                raise ValidationExceptionError(e.msg, e.key, e.status)
            except LedgerError as e:
                for instance in ledger_data["instances"]:
                    instance.delete()
                raise LedgerExceptionError(str(e.msg), e.status)
            except (ValidationExceptionError, serializers.ValidationError):
                for instance in ledger_data["instances"]:
                    instance.delete()
                raise

            data = []
            for instance in instances:
                serializer = self.get_serializer(instance)
                if (
                    "key" in ledger_result and
                    ledger_result["validated"] and
                    serializer.data["key"] in ledger_result["key"]
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
    def _ledger_create(ledger_data, channel_name):
        ledger_serializer = LedgerDataSampleSerializer(data=ledger_data)
        if not ledger_serializer.is_valid():
            raise serializers.ValidationError(ledger_serializer.errors)
        return ledger_serializer.create(
            channel_name,
            ledger_serializer.validated_data,
        )

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
            data = query_ledger(get_channel_name(request), fcn="queryDataSamples", args=[])
        except LedgerError as e:
            return Response({"message": str(e.msg)}, status=e.status)

        data = data or []

        return self.paginate_response(data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=False)
    def bulk_update(self, request):
        ledger_serializer = LedgerDataSampleUpdateSerializer(data=dict(request.data))
        ledger_serializer.is_valid(raise_exception=True)

        try:
            data = ledger_serializer.create(get_channel_name(request), ledger_serializer.validated_data)
        except LedgerError as e:
            return Response({"message": str(e.msg)}, status=e.status)

        if settings.LEDGER_SYNC_ENABLED:
            st = status.HTTP_200_OK
        else:
            st = status.HTTP_202_ACCEPTED

        return Response(data, status=st)


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
