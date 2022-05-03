import structlog
from rest_framework.viewsets import GenericViewSet

import orchestrator.common_pb2 as common_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
from libs.pagination import DefaultPageNumberPagination
from localrep.models import Algo as AlgoRep
from localrep.models import ComputePlan as ComputePlanRep
from localrep.models import DataManager as DataManagerRep
from localrep.models import Metric as MetricRep
from substrapp.views.utils import get_channel_name

logger = structlog.get_logger(__name__)

PLAN_STATUS_CREATED = "STATUS_CREATED"  # no protobuf value as it is specific to news feed


def cp_item(key, name, status, date, detail=None):
    """Newsfeed items specific to computeplan"""
    return {
        "asset_kind": common_pb2.AssetKind.Name(common_pb2.ASSET_COMPUTE_PLAN),
        "asset_key": key,
        "name": name,
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
        channel = get_channel_name(request)

        for compute_plan in ComputePlanRep.objects.filter(channel=channel):
            status = PLAN_STATUS_CREATED
            items.append(
                cp_item(
                    compute_plan.key,
                    compute_plan.metadata.get("name", compute_plan.tag),
                    status,
                    compute_plan.creation_date,
                )
            )
            if compute_plan.start_date:
                status = computeplan_pb2.ComputePlanStatus.Name(computeplan_pb2.PLAN_STATUS_DOING)
                items.append(
                    cp_item(
                        compute_plan.key,
                        compute_plan.metadata.get("name", compute_plan.tag),
                        status,
                        compute_plan.start_date,
                    )
                )
            if compute_plan.end_date:
                status = computeplan_pb2.ComputePlanStatus.Name(compute_plan.status)
                detail = {}
                if compute_plan.failed_task_key:
                    detail["first_failed_task_key"] = compute_plan.failed_task_key
                    detail["task_category"] = compute_plan.failed_task_category
                items.append(
                    cp_item(
                        compute_plan.key,
                        compute_plan.metadata.get("name", compute_plan.tag),
                        status,
                        compute_plan.end_date,
                        detail,
                    )
                )

        for algo in AlgoRep.objects.filter(channel=channel):
            items.append(
                {
                    "asset_kind": common_pb2.AssetKind.Name(common_pb2.ASSET_ALGO),
                    "asset_key": algo.key,
                    "name": algo.name,
                    "status": "STATUS_CREATED",
                    "timestamp": algo.creation_date,
                    "detail": {},
                }
            )

        for datamanager in DataManagerRep.objects.filter(channel=channel):
            items.append(
                {
                    "asset_kind": common_pb2.AssetKind.Name(common_pb2.ASSET_DATA_MANAGER),
                    "asset_key": datamanager.key,
                    "name": datamanager.name,
                    "status": "STATUS_CREATED",
                    "timestamp": datamanager.creation_date,
                    "detail": {},
                }
            )

        # This block will be removed once metrics are merged into algos in localrep
        for metric in MetricRep.objects.filter(channel=channel):
            items.append(
                {
                    "asset_kind": "ASSET_METRIC",
                    "asset_key": metric.key,
                    "name": metric.name,
                    "status": "STATUS_CREATED",
                    "timestamp": metric.creation_date,
                    "detail": {},
                }
            )

        items.sort(key=lambda x: x["timestamp"], reverse=True)
        items = self.paginate_queryset(items)
        return self.get_paginated_response(items)
