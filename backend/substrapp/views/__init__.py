from .algo import AlgoPermissionViewSet
from .algo import AlgoViewSet
from .algo import CPAlgoViewSet
from .computeplan import ComputePlanViewSet
from .computetask import ComputeTaskViewSet
from .computetask import CPTaskViewSet
from .computetask_logs import ComputeTaskLogsViewSet
from .datamanager import DataManagerPermissionViewSet
from .datamanager import DataManagerViewSet
from .datasample import DataSampleViewSet
from .metadata import ComputePlanMetadataViewSet
from .model import ModelPermissionViewSet
from .model import ModelViewSet
from .newsfeed import NewsFeedViewSet
from .performance import CPPerformanceViewSet

__all__ = [
    "DataSampleViewSet",
    "DataManagerViewSet",
    "DataManagerPermissionViewSet",
    "ModelViewSet",
    "ModelPermissionViewSet",
    "AlgoViewSet",
    "AlgoPermissionViewSet",
    "ComputeTaskViewSet",
    "ComputePlanViewSet",
    "CPTaskViewSet",
    "CPAlgoViewSet",
    "NewsFeedViewSet",
    "ComputeTaskLogsViewSet",
    "CPPerformanceViewSet",
    "ComputePlanMetadataViewSet",
]
