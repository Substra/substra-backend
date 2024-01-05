from rest_framework import response as drf_response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action

from api.errors import AssetPermissionError
from api.models import ComputeTask
from api.models import Function
from api.views import utils as view_utils
from substrapp.models import asset_failure_report


class FailedAssetLogsViewSet(view_utils.PermissionMixin, viewsets.GenericViewSet):
    queryset = asset_failure_report.AssetFailureReport.objects.all()

    @action(detail=True, url_path=asset_failure_report.LOGS_FILE_PATH)
    def file(self, request, pk=None) -> drf_response.Response:
        report = self.get_object()
        channel_name = view_utils.get_channel_name(request)
        if report.asset_type == asset_failure_report.FailedAssetKind.FAILED_ASSET_FUNCTION:
            asset_class = Function
        else:
            asset_class = ComputeTask

        key = str(report.key)
        try:
            asset = self.get_asset(request, key, channel_name, asset_class)
        except AssetPermissionError as e:
            return view_utils.ApiResponse({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        response = view_utils.get_file_response(
            local_file_class=asset_failure_report.AssetFailureReport,
            key=key,
            content_field="logs",
            channel_name=channel_name,
            url=report.logs_address,
            asset_owner=asset.get_owner(),
        )

        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.headers["Content-Disposition"] = f'attachment; filename="tuple_logs_{pk}.txt"'
        return response
