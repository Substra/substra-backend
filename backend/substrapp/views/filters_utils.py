import structlog
from django.db.models import Q
from rest_framework.filters import BaseFilterBackend

logger = structlog.get_logger(__name__)


class PermissionFilter(BaseFilterBackend):
    """Filter assets who can be used by a given set of organizations"""

    def get_param(self):
        try:
            return self.param
        except AttributeError:
            raise NotImplementedError("Missing param definition")

    def get_field(self):
        try:
            return self.field
        except AttributeError:
            raise NotImplementedError("Missing field definition")

    def get_organization_ids(self, request):
        params = request.query_params.get(self.get_param())
        if params:
            organization_ids = [param.strip() for param in params.split(",")]
            return organization_ids
        return []

    def filter_queryset(self, request, queryset, view):
        organization_ids = self.get_organization_ids(request)
        if organization_ids:
            is_public = Q(**{f"{self.get_field()}_public": True})
            is_authorized = Q(**{f"{self.get_field()}_authorized_ids__contains": organization_ids})
            queryset = queryset.filter(is_public | is_authorized)
        return queryset


class ProcessPermissionFilter(PermissionFilter):
    param = "can_process"
    field = "permissions_process"


class LogsPermissionFilter(PermissionFilter):
    param = "can_access_logs"
    field = "logs_permission"
