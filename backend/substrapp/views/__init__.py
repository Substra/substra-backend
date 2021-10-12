# encoding: utf-8

from .datasample import DataSampleViewSet
from .datamanager import DataManagerViewSet, DataManagerPermissionViewSet
from .metric import MetricViewSet, MetricPermissionViewSet
from .model import ModelViewSet, ModelPermissionViewSet
from .algo import AlgoViewSet, AlgoPermissionViewSet
from .computetask import ComputeTaskViewSet
from .computeplan import ComputePlanViewSet, CPTaskViewSet

__all__ = [
    'DataSampleViewSet',
    'DataManagerViewSet',
    'DataManagerPermissionViewSet',
    'MetricViewSet',
    'MetricPermissionViewSet',
    'ModelViewSet',
    'ModelPermissionViewSet',
    'AlgoViewSet',
    'AlgoPermissionViewSet',
    'ComputeTaskViewSet',
    'ComputePlanViewSet',
    'CPTaskViewSet',
]
