import structlog
from rest_framework.viewsets import GenericViewSet

import orchestrator.common_pb2 as common_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
from libs.pagination import DefaultPageNumberPagination
from localrep.models import ComputePlan as ComputePlanRep
from substrapp.views.utils import get_channel_name

logger = structlog.get_logger(__name__)

PLAN_STATUS_CREATED = "STATUS_CREATED"  # no protobuf value as it is specific to news feed


def cp_item(key, status, date, detail=None):
    """Newsfeed items specific to computeplan"""
    return {
        "asset_kind": common_pb2.AssetKind.Name(common_pb2.ASSET_COMPUTE_PLAN),
        "asset_key": key,
        "status": status.removeprefix("PLAN_"),
        "timestamp": date,
        "detail": detail or {},
    }


class NewsFeedViewSet(GenericViewSet):

    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return []

    def list(self, request):
        """
        Newsfeed items include:
            - ASSET_COMPUTE_PLAN:
                - STATUS_CREATED with computeplan creation_date
                - STATUS_DOING with computeplan start_date
                - STATUS_DONE/FAILED/CANCELED with computeplan end_date
        """

        items = []
        for compute_plan in ComputePlanRep.objects.filter(channel=get_channel_name(request)):
            status = PLAN_STATUS_CREATED
            items.append(cp_item(compute_plan.key, status, compute_plan.creation_date))
            if compute_plan.start_date:
                status = computeplan_pb2.ComputePlanStatus.Name(computeplan_pb2.PLAN_STATUS_DOING)
                items.append(cp_item(compute_plan.key, status, compute_plan.start_date))
            if compute_plan.end_date:
                status = computeplan_pb2.ComputePlanStatus.Name(compute_plan.status)
                detail = {}
                if compute_plan.failed_task_key:
                    detail["first_failed_task_key"] = compute_plan.failed_task_key
                    detail["task_category"] = compute_plan.failed_task_category
                items.append(cp_item(compute_plan.key, status, compute_plan.end_date, detail))

        items.sort(key=lambda x: x["timestamp"], reverse=True)
        items = self.paginate_queryset(items)
        return self.get_paginated_response(items)
