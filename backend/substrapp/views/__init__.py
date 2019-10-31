# encoding: utf-8

from .datasample import DataSampleViewSet
from .datamanager import DataManagerViewSet, DataManagerPermissionViewSet
from .objective import ObjectiveViewSet, ObjectivePermissionViewSet
from .model import ModelViewSet, ModelPermissionViewSet
from .algo import AlgoViewSet, AlgoPermissionViewSet
from .traintuple import TrainTupleViewSet
from .testtuple import TestTupleViewSet
from .task import TaskViewSet
from .computeplan import ComputePlanViewSet
from .compositetraintuple import CompositeTraintupleViewSet
from .compositealgo import CompositeAlgoViewSet, CompositeAlgoPermissionViewSet

__all__ = ['DataSampleViewSet', 'DataManagerViewSet', 'DataManagerPermissionViewSet', 'ObjectiveViewSet',
           'ObjectivePermissionViewSet', 'ModelViewSet', 'ModelPermissionViewSet', 'AlgoViewSet',
           'AlgoPermissionViewSet', 'TrainTupleViewSet', 'TestTupleViewSet', 'TaskViewSet', 'ComputePlanViewSet',
           'CompositeTraintupleViewSet', 'CompositeAlgoViewSet', 'CompositeAlgoPermissionViewSet'
           ]
