import structlog
from django.db.models import Func
from rest_framework.viewsets import GenericViewSet

from api.models import ComputePlan as ComputePlan
from api.views.utils import ApiResponse
from api.views.utils import get_channel_name

logger = structlog.get_logger(__name__)


class JsonbKeys(Func):
    function = "jsonb_object_keys"


class ComputePlanMetadataViewSet(GenericViewSet):
    def list(self, request):
        return ApiResponse(
            ComputePlan.objects.filter(channel=get_channel_name(self.request))
            .annotate(metadata_keys=JsonbKeys("metadata"))
            .order_by("metadata_keys")
            .values_list("metadata_keys", flat=True)
            .distinct("metadata_keys")
        )
