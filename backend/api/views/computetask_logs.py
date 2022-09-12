from rest_framework import response as drf_response
from rest_framework import viewsets
from rest_framework.decorators import action

from api.models import ComputeTask
from api.views import utils as view_utils
from substrapp.models import compute_task_failure_report


class ComputeTaskLogsViewSet(view_utils.PermissionMixin, viewsets.GenericViewSet):
    queryset = compute_task_failure_report.ComputeTaskFailureReport.objects.all()

    @action(detail=True, url_path=compute_task_failure_report.LOGS_FILE_PATH)
    def file(self, request, pk=None) -> drf_response.Response:
        response = self.download_file(request, ComputeTask, "logs", "logs_address")
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.headers["Content-Disposition"] = f'attachment; filename="tuple_logs_{pk}.txt"'
        return response
