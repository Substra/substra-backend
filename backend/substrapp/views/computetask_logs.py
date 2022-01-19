from rest_framework import response as drf_response
from rest_framework import viewsets
from rest_framework.decorators import action

from substrapp.models import compute_task_failure_report
from substrapp.orchestrator import get_orchestrator_client
from substrapp.views import utils as view_utils


class ComputeTaskLogsViewSet(viewsets.GenericViewSet, view_utils.PermissionMixin):
    queryset = compute_task_failure_report.ComputeTaskFailureReport.objects.all()

    @action(detail=True, url_path=compute_task_failure_report.LOGS_FILE_PATH)
    def file(self, request, pk=None) -> drf_response.Response:
        response = self.download_file(
            request, query_method="query_task", django_field="logs", orchestrator_field="logs_address"
        )
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.headers["Content-Disposition"] = f'attachment; filename="tuple_logs_{pk}.txt"'
        return response

    def get_permission(self, asset):
        return asset["logs_permission"]

    def get_storage_address(self, asset, ledger_field) -> str:
        with get_orchestrator_client(view_utils.get_channel_name(self.request)) as client:
            failure = client.get_failure_report({"compute_task_key": asset["key"]})

        return super().get_storage_address(failure, ledger_field)
