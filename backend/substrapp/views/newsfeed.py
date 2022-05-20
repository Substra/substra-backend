import structlog
from rest_framework.viewsets import GenericViewSet

import orchestrator.common_pb2 as common_pb2
from libs.pagination import DefaultPageNumberPagination
from localrep.models import Algo as AlgoRep
from localrep.models import ComputePlan as ComputePlanRep
from localrep.models import DataManager as DataManagerRep
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

    def date_filters(self, field):
        timestamp_after = self.request.query_params.get("timestamp_after")
        timestamp_before = self.request.query_params.get("timestamp_before")
        filters = {}
        if timestamp_after:
            filters[f"{field}__gte"] = timestamp_after
        if timestamp_before:
            filters[f"{field}__lt"] = timestamp_before
        return filters

    def get_compute_plan_items(self, is_important_news_only: bool = False):
        items = []
        channel = get_channel_name(self.request)

        for compute_plan in ComputePlanRep.objects.filter(
            channel=channel, end_date__isnull=False, **self.date_filters("end_date")
        ):
            detail = {}
            if compute_plan.failed_task_key:
                detail["first_failed_task_key"] = compute_plan.failed_task_key
                detail["task_category"] = compute_plan.failed_task_category
            items.append(
                cp_item(
                    compute_plan.key,
                    compute_plan.metadata.get("name", compute_plan.tag),
                    compute_plan.status,
                    compute_plan.end_date,
                    detail,
                )
            )

        # only cp end is considered as important news
        if is_important_news_only:
            return items

        # else retrieve all other news
        for compute_plan in ComputePlanRep.objects.filter(channel=channel, **self.date_filters("creation_date")):
            items.append(
                cp_item(
                    compute_plan.key,
                    compute_plan.metadata.get("name", compute_plan.tag),
                    PLAN_STATUS_CREATED,
                    compute_plan.creation_date,
                )
            )

        for compute_plan in ComputePlanRep.objects.filter(
            channel=channel, start_date__isnull=False, **self.date_filters("start_date")
        ):
            items.append(
                cp_item(
                    compute_plan.key,
                    compute_plan.metadata.get("name", compute_plan.tag),
                    ComputePlanRep.Status.PLAN_STATUS_DOING,
                    compute_plan.start_date,
                )
            )

        return items

    def get_algo_items(self):
        items = []
        channel = get_channel_name(self.request)

        for algo in AlgoRep.objects.filter(channel=channel, **self.date_filters("creation_date")):

            # This block will be removed once metric concept is fully merged into algo
            if algo.category == AlgoRep.Category.ALGO_METRIC:
                asset_kind = "ASSET_METRIC"
            else:
                asset_kind = common_pb2.AssetKind.Name(common_pb2.ASSET_ALGO)

            items.append(
                {
                    "asset_kind": asset_kind,
                    "asset_key": algo.key,
                    "name": algo.name,
                    "status": "STATUS_CREATED",
                    "timestamp": algo.creation_date,
                    "detail": {},
                }
            )
        return items

    def get_datamanager_items(self):
        items = []
        channel = get_channel_name(self.request)

        for datamanager in DataManagerRep.objects.filter(channel=channel, **self.date_filters("creation_date")):
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
        return items

    def list(self, request):
        """
        Newsfeed items include:
            - ASSET_COMPUTE_PLAN:
                - STATUS_CREATED with computeplan creation_date
                - STATUS_DOING with computeplan start_date
                - STATUS_DONE/FAILED/CANCELED with computeplan end_date
            - ASSET_ALGO:
                - STATUS_CREATED with algo/metric creation_date
            - ASSET_DATAMANGER:
                - STATUS_CREATED with datamanager creation_date

        Important newsfeed items include:
            - ASSET_COMPUTE_PLAN:
                - STATUS_DONE/FAILED/CANCELED with computeplan end_date
        """
        is_important_news_only = self.request.query_params.get("important_news_only") == "true"
        if is_important_news_only:
            items = self.get_compute_plan_items(is_important_news_only)
        else:
            items = (
                self.get_compute_plan_items(is_important_news_only)
                + self.get_algo_items()
                + self.get_datamanager_items()
            )
        items.sort(key=lambda x: x["timestamp"], reverse=True)
        items = self.paginate_queryset(items)
        return self.get_paginated_response(items)
