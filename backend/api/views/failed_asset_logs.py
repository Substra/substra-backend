from rest_framework import response as drf_response
from rest_framework import viewsets
from rest_framework.decorators import action
from api.models import ComputeTask
from api.views import utils as view_utils
from substrapp.models import asset_failure_report
from substrapp.models import FailedAssetKind


class FailedAssetLogsViewSet(view_utils.PermissionMixin, viewsets.GenericViewSet):
    queryset = asset_failure_report.AssetFailureReport.objects.all()


    def get_asset_key(self, request) -> str:
        compute_task_key = super().get_asset_key(request)
        queryset = self.filter_queryset(self.get_queryset())

    @action(detail=True, url_path=asset_failure_report.LOGS_FILE_PATH)
    def file(self, request, pk=None) -> drf_response.Response:
        report = self.get_object()

        if report.asset_type == asset_failure_report.FailedAssetKind.FAILED_ASSET_FUNCTION:
            asset_type = Function
        else:
            asset_type = ComputeTask

        response = self.download_file(request, ComputeTask, "logs", "logs_address")
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.headers["Content-Disposition"] = f'attachment; filename="tuple_logs_{pk}.txt"'
        return response
