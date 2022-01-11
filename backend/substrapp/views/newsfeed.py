from collections import namedtuple

import structlog
from rest_framework.viewsets import GenericViewSet

import orchestrator.common_pb2 as common_pb2
import orchestrator.computeplan_pb2 as computeplan_pb2
import orchestrator.computetask_pb2 as computetask_pb2
import orchestrator.event_pb2 as event_pb2
from libs.pagination import DefaultPageNumberPagination
from libs.pagination import PaginationMixin
from substrapp.orchestrator import get_orchestrator_client
from substrapp.views.utils import get_channel_name

logger = structlog.get_logger(__name__)

ASSET_COMPUTE_PLAN = common_pb2.AssetKind.Name(common_pb2.ASSET_COMPUTE_PLAN)
ASSET_COMPUTE_TASK = common_pb2.AssetKind.Name(common_pb2.ASSET_COMPUTE_TASK)
EVENT_ASSET_CREATED = event_pb2.EventKind.Name(event_pb2.EVENT_ASSET_CREATED)
EVENT_ASSET_UPDATED = event_pb2.EventKind.Name(event_pb2.EVENT_ASSET_UPDATED)
PLAN_STATUS_CREATED = "STATUS_CREATED"  # no protobuf value as it is specific to news feed
PLAN_STATUS_DONE = computeplan_pb2.ComputePlanStatus.Name(computeplan_pb2.PLAN_STATUS_DONE)
TASK_STATUS_DOING = computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_DOING)
TASK_STATUS_DONE = computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_DONE)
TASK_STATUS_FAILED = computetask_pb2.ComputeTaskStatus.Name(computetask_pb2.STATUS_FAILED)


class NewsFeedViewSet(GenericViewSet, PaginationMixin):

    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return []

    def list(self, request):
        """
        Returns all feed items for the task and compute plan assets.

        Feed items include:
        - created compute plans
        - task status updates

        For each task and each compute plan, there is at most one feed item.
        """
        with get_orchestrator_client(get_channel_name(request)) as client:
            cp_events = client.query_events(asset_kind=ASSET_COMPUTE_PLAN, event_kind=EVENT_ASSET_CREATED)
            task_events = client.query_events(asset_kind=ASSET_COMPUTE_TASK, event_kind=EVENT_ASSET_UPDATED)
        feed_items = {}
        # We use a custom key composed of the CP key and event task status.
        # This allows us to quickly verify the existence of an item.
        FeedItemKey = namedtuple("Feed_item_key", ["compute_plan_key", "feed_item_status"])

        feed_item_status = PLAN_STATUS_CREATED
        for event in cp_events:
            feed_item_key = FeedItemKey(event["asset_key"], feed_item_status)
            feed_items[feed_item_key] = {
                "asset_kind": event["asset_kind"],
                "asset_key": event["asset_key"],
                "status": feed_item_status,
                "timestamp": event["timestamp"],
                "detail": {},
            }

        for event in task_events:
            compute_task_status = event["metadata"]["status"]
            if compute_task_status not in [TASK_STATUS_DOING, TASK_STATUS_DONE, TASK_STATUS_FAILED]:
                continue  # Skip event
            feed_item_key = FeedItemKey(event["metadata"]["compute_plan_key"], compute_task_status)

            # There are multiple compute tasks for the same compute plan
            # but we only want one news item per status for each compute plan.
            # Search existing news for current compute plan
            if feed_item_key in feed_items:
                continue  # Skip event

            # For event task doing, skip event if related compute plan is failed
            if (
                compute_task_status == TASK_STATUS_DOING
                and (event["metadata"]["compute_plan_key"], TASK_STATUS_FAILED) in feed_items
            ):
                continue

            with get_orchestrator_client(get_channel_name(request)) as client:
                compute_plan = client.query_compute_plan(event["metadata"]["compute_plan_key"])
            # Register the last done compute task event by checking compute plan status
            if compute_task_status == TASK_STATUS_DONE and compute_plan["status"] != PLAN_STATUS_DONE:
                # next event
                continue

            item_details = {}
            if compute_task_status == TASK_STATUS_FAILED:
                item_details = {"first_failed_task_key": event["asset_key"]}

            # No news found so create one
            feed_items[feed_item_key] = {
                "asset_kind": ASSET_COMPUTE_PLAN,
                "asset_key": event["metadata"]["compute_plan_key"],
                "status": compute_task_status,
                "timestamp": event["timestamp"],
                "detail": item_details,
            }

        sorted_feed_item = sorted(feed_items.values(), key=lambda x: x["timestamp"], reverse=True)

        return self.paginate_response(list(sorted_feed_item))
