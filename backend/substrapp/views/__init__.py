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
from .metric import MetricPermissionViewSet
from .metric import MetricViewSet
from .model import ModelPermissionViewSet
from .model import ModelViewSet
from .newsfeed import NewsFeedViewSet

__all__ = [
    "DataSampleViewSet",
    "DataManagerViewSet",
    "DataManagerPermissionViewSet",
    "MetricViewSet",
    "MetricPermissionViewSet",
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
]
