import structlog
import uuid

from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from substrapp import exceptions
from substrapp.serializers import (
    OrchestratorComputePlanSerializer,
    OrchestratorTrainTaskSerializer,
    OrchestratorCompositeTrainTaskSerializer,
    OrchestratorAggregateTaskSerializer,
    OrchestratorTestTaskSerializer
)
from substrapp.views.filters_utils import filter_list
from libs.pagination import DefaultPageNumberPagination, PaginationMixin
from substrapp.views.utils import (
    ValidationExceptionError,
    get_channel_name,
    validate_key)
from substrapp.views.utils import TASK_CATEGORY, add_task_extra_information
from substrapp.orchestrator import get_orchestrator_client
from orchestrator.error import OrcError

logger = structlog.get_logger(__name__)


def create_compute_plan(request, data):
    serializer = OrchestratorComputePlanSerializer(data=data, context={'request': request})
    try:
        serializer.is_valid(raise_exception=True)
    except Exception as e:
        raise ValidationExceptionError(e.args, '(not computed)', status.HTTP_400_BAD_REQUEST)
    return serializer.create(get_channel_name(request), serializer.validated_data)


class ComputePlanViewSet(mixins.CreateModelMixin,
                         PaginationMixin,
                         GenericViewSet):

    serializer_class = OrchestratorComputePlanSerializer
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return []

    def parse_traintuples(self, request, traintuples, compute_plan_key):
        tasks = {}
        for traintuple in traintuples:
            data = {
                'key': traintuple.get('traintuple_id'),
                'category': TASK_CATEGORY['traintuple'],
                'algo_key': traintuple.get('algo_key'),
                'compute_plan_key': compute_plan_key,
                'metadata': traintuple.get('metadata'),
                'parent_task_keys': traintuple.get('in_models_ids', []),
                'tag': traintuple.get('tag', ''),
                'data_manager_key': traintuple.get('data_manager_key'),
                'data_sample_keys': traintuple.get('train_data_sample_keys')
            }
            orchestrator_serializer = OrchestratorTrainTaskSerializer(
                data=data,
                context={
                    'request': request
                }
            )

            try:
                orchestrator_serializer.is_valid(raise_exception=True)
            except Exception as e:
                raise ValidationExceptionError(e.args, '(not computed)', status.HTTP_400_BAD_REQUEST)

            task_data = orchestrator_serializer.get_args(orchestrator_serializer.validated_data)

            tasks[task_data['key']] = task_data
        return tasks

    def parse_composite_traintuple(self, request, composites, compute_plan_key):
        tasks = {}
        for composite in composites:
            parent_task_keys = [composite.get('in_head_model_id'), composite.get('in_trunk_model_id')]
            data = {
                'key': composite.get('composite_traintuple_id'),
                'category': TASK_CATEGORY['composite_traintuple'],
                'algo_key': composite.get('algo_key'),
                'compute_plan_key': compute_plan_key,
                'metadata': composite.get('metadata'),
                'parent_task_keys': [item for item in parent_task_keys if item],
                'tag': composite.get('tag', ''),
                'data_manager_key': composite.get('data_manager_key'),
                'data_sample_keys': composite.get('train_data_sample_keys'),
                'trunk_permissions': composite.get('out_trunk_model_permissions'),
            }

            orchestrator_serializer = OrchestratorCompositeTrainTaskSerializer(
                data=data,
                context={
                    'request': request
                }
            )

            try:
                orchestrator_serializer.is_valid(raise_exception=True)
            except Exception as e:
                raise ValidationExceptionError(e.args, '(not computed)', status.HTTP_400_BAD_REQUEST)

            task_data = orchestrator_serializer.get_args(orchestrator_serializer.validated_data)
            logger.debug(task_data)
            tasks[task_data['key']] = task_data
        return tasks

    def parse_aggregate_traintuple(self, request, aggregates, compute_plan_key):
        tasks = {}
        for aggregate in aggregates:
            data = {
                'key': aggregate.get('aggregatetuple_id'),
                'category': TASK_CATEGORY['aggregatetuple'],
                'algo_key': aggregate.get('algo_key'),
                'compute_plan_key': compute_plan_key,
                'metadata': aggregate.get('metadata'),
                'parent_task_keys': aggregate.get('in_models_ids', []),
                'tag': aggregate.get('tag', ''),
                'worker': aggregate.get('worker')
            }

            orchestrator_serializer = OrchestratorAggregateTaskSerializer(
                data=data,
                context={
                    'request': request
                }
            )

            try:
                orchestrator_serializer.is_valid(raise_exception=True)
            except Exception as e:
                raise ValidationExceptionError(e.args, '(not computed)', status.HTTP_400_BAD_REQUEST)

            task_data = orchestrator_serializer.get_args(orchestrator_serializer.validated_data)

            tasks[task_data['key']] = task_data
        return tasks

    def parse_testtuple(self, request, testtuples, compute_plan_key, compute_tasks):
        tasks = {}
        for testtuple in testtuples:
            data = {
                'key': uuid.uuid4(),
                'category': TASK_CATEGORY['testtuple'],
                'compute_plan_key': compute_plan_key,
                'metadata': testtuple.get('metadata'),
                'tag': testtuple.get('tag', ''),
                'objective_key': testtuple.get('objective_key'),
                'data_manager_key': testtuple.get('data_manager_key'),
                'data_sample_keys': testtuple.get('test_data_sample_keys'),
                'parent_task_keys': []
            }

            if testtuple.get('traintuple_id'):
                data['parent_task_keys'].append(testtuple.get('traintuple_id'))
                algo_key = compute_tasks.get(testtuple.get('traintuple_id'), {}).get('algo_key')
                if algo_key:
                    data['algo_key'] = algo_key
                else:
                    # The training task might already be registered and not part of the current batch
                    with get_orchestrator_client(get_channel_name(request)) as client:
                        task = client.query_task(testtuple.get('traintuple_id'))
                        data['algo_key'] = task['algo']['key']
            else:
                raise ValidationExceptionError(
                    data=[{'traintuple_id': ['This field may not be null.']}],
                    key=data['key'],
                    st=status.HTTP_400_BAD_REQUEST
                )

            orchestrator_serializer = OrchestratorTestTaskSerializer(
                data=data,
                context={
                    'request': request
                }
            )

            try:
                orchestrator_serializer.is_valid(raise_exception=True)
            except Exception as e:
                raise ValidationExceptionError(e.args, '(not computed)', status.HTTP_400_BAD_REQUEST)

            task_data = orchestrator_serializer.get_args(orchestrator_serializer.validated_data)

            tasks[task_data['key']] = task_data
        return tasks

    def commit(self, request):
        compute_plan_data = {
            'key': uuid.uuid4(),
            'tag': request.data.get('tag'),
            'metadata': request.data.get('metadata'),
            'delete_intermediary_models': request.data.get('clean_models', False),
        }
        # To handle later
        traintuples = request.data.get('traintuples', [])
        validated_traintuples = self.parse_traintuples(request, traintuples, compute_plan_data['key'])
        composites = request.data.get('composite_traintuples', [])
        validated_composites = self.parse_composite_traintuple(request, composites, compute_plan_data['key'])
        aggregatetuples = request.data.get('aggregatetuples', [])
        validated_aggregates = self.parse_aggregate_traintuple(request, aggregatetuples, compute_plan_data['key'])
        testtuples = request.data.get('testtuples', [])
        validated_testtuples = self.parse_testtuple(
            request,
            testtuples,
            compute_plan_data['key'],
            {**validated_traintuples, **validated_composites, **validated_aggregates}
        )

        tasks = (
            list(validated_traintuples.values()) +
            list(validated_composites.values()) +
            list(validated_aggregates.values()) +
            list(validated_testtuples.values())
        )

        cp = create_compute_plan(request, data=compute_plan_data)

        if tasks:
            with get_orchestrator_client(get_channel_name(request)) as client:
                client.register_tasks({"tasks": tasks})

        return cp

    def create(self, request, *args, **kwargs):
        try:
            data = self.commit(request)
        except ValidationExceptionError as e:
            return Response({'message': e.data, 'key': e.key}, status=e.st)
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            headers = self.get_success_headers(data)
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        validate_key(key)

        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                data = client.query_compute_plan(key)
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except exceptions.BadRequestError:
            raise
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                data = client.query_compute_plans()
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        query_params = request.query_params.get('search')
        if query_params is not None:
            try:
                data = filter_list(
                    object_type='compute_plan',
                    data=data,
                    query_params=query_params)
            except OrcError as rpc_error:
                return Response({'message': rpc_error.details}, status=rpc_error.http_status())
            except Exception as e:
                logger.exception(e)
                return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return self.paginate_response(data)

    @action(detail=True, methods=['POST'])
    def cancel(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        validate_key(key)

        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                client.cancel_compute_plan(key)
                compute_plan = client.query_compute_plan(key)
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(compute_plan, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def update_ledger(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        validate_key(key)

        traintuples = request.data.get('traintuples', [])
        validated_traintuples = self.parse_traintuples(request, traintuples, key)
        composites = request.data.get('composite_traintuples', [])
        validated_composites = self.parse_composite_traintuple(request, composites, key)
        aggregatetuples = request.data.get('aggregatetuples', [])
        validated_aggregates = self.parse_aggregate_traintuple(request, aggregatetuples, key)
        testtuples = request.data.get('testtuples', [])
        validated_testtuples = self.parse_testtuple(
            request,
            testtuples,
            key,
            {**validated_traintuples, **validated_composites, **validated_aggregates}
        )

        tasks = (
            list(validated_traintuples.values()) +
            list(validated_composites.values()) +
            list(validated_aggregates.values()) +
            list(validated_testtuples.values())
        )

        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                client.register_tasks({
                    "tasks": tasks
                })
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({}, status=status.HTTP_200_OK)


class GenericSubassetViewset(PaginationMixin,
                             GenericViewSet):

    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return []

    def list(self, request, compute_plan_pk, basename):
        if not self.is_page_size_param_present():
            # We choose to force the page_size parameter in these views in order to limit the number of queries
            # to the chaincode
            return Response(status=status.HTTP_400_BAD_REQUEST, data='page_size param is required')

        validate_key(compute_plan_pk)

        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                data = client.query_tasks(
                    category=TASK_CATEGORY[basename],
                    compute_plan_key=compute_plan_pk)
                for datum in data:
                    datum = add_task_extra_information(client, basename, datum)
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        query_params = request.query_params.get('search')
        if query_params is not None:
            try:
                data = filter_list(
                    object_type=basename,
                    data=data,
                    query_params=query_params)
            except OrcError as rpc_error:
                return Response({'message': rpc_error.details}, status=rpc_error.http_status())
            except Exception as e:
                logger.exception(e)
                return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return self.paginate_response(data)


class CPTaskViewSet(GenericSubassetViewset):

    def list(self, request, compute_plan_pk):

        return super().list(
            request=request,
            compute_plan_pk=compute_plan_pk,
            basename=self.basename.removeprefix("compute_plan_"))
