import tempfile

from django.http import Http404
from django.urls import reverse
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp import exceptions
from substrapp.models import Objective
from substrapp.serializers import ObjectiveSerializer, OrchestratorObjectiveSerializer

from substrapp.utils import get_hash
from substrapp.views.utils import (PermissionMixin, ValidationExceptionError, validate_key,
                                   get_remote_asset, validate_sort, node_has_process_permission,
                                   get_channel_name)
from substrapp.views.filters_utils import filter_list
from libs.pagination import DefaultPageNumberPagination, PaginationMixin

from substrapp.orchestrator import get_orchestrator_client
from orchestrator.error import OrcError

import structlog

logger = structlog.get_logger(__name__)


def replace_storage_addresses(request, objective):
    objective['description']['storage_address'] = request.build_absolute_uri(
        reverse('substrapp:objective-description', args=[objective['key']]))
    objective['metrics']['storage_address'] = request.build_absolute_uri(
        reverse('substrapp:objective-metrics', args=[objective['key']])
    )


class ObjectiveViewSet(mixins.CreateModelMixin,
                       PaginationMixin,
                       GenericViewSet):
    queryset = Objective.objects.all()
    serializer_class = ObjectiveSerializer
    pagination_class = DefaultPageNumberPagination

    def commit(self, serializer, request):
        # create on db
        instance = serializer.save()

        # serialized data for orchestrator db
        orchestrator_serializer = OrchestratorObjectiveSerializer(
            data={
                'name': request.data.get('name'),
                'data_sample_keys': request.data.get('test_data_sample_keys') or [],
                'data_manager_key': request.data.get('test_data_manager_key'),
                'permissions': request.data.get('permissions'),
                'metrics_name': request.data.get('metrics_name'),
                'metadata': request.data.get('metadata'),
                'instance': instance
            },
            context={
                'request': request
            }
        )
        if not orchestrator_serializer.is_valid():
            instance.delete()
            raise ValidationError(orchestrator_serializer.errors)

        # create on orchestrator db
        try:
            data = orchestrator_serializer.create(
                get_channel_name(request),
                orchestrator_serializer.validated_data
            )
        except Exception:
            instance.delete()
            raise

        merged_data = dict(serializer.data)
        merged_data.update(data)

        return merged_data

    def _create(self, request):
        description = request.data.get('description')
        try:
            checksum = get_hash(description)
        except Exception as e:
            raise ValidationExceptionError(e.args, '(not computed)', status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={
            'metrics': request.data.get('metrics'),
            'description': description,
            'checksum': checksum
        })

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise ValidationExceptionError(e.args, '(not computed)', status.HTTP_400_BAD_REQUEST)
        else:
            return self.commit(serializer, request)

    def create(self, request, *args, **kwargs):

        try:
            data = self._create(request)
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

    def create_or_update_objective_description(self, channel_name, objective, key):
        # We need to have, at least, objective description for the frontend
        content = get_remote_asset(
            channel_name=channel_name,
            url=objective['description']['storage_address'],
            node_id=objective['owner'],
            content_checksum=objective['description']['checksum']
        )

        description_file = tempfile.TemporaryFile()
        description_file.write(content)

        instance, created = Objective.objects.update_or_create(key=key, validated=True)
        instance.description.save('description.md', description_file)

        return instance

    def _retrieve(self, request, key):
        validate_key(key)

        with get_orchestrator_client(get_channel_name(request)) as client:
            data = client.query_objective(key)

        # verify if objectve description exists for the frontend view
        # if not fetch it if it's possible
        # do not fetch  objectve description if node has not process permission
        if node_has_process_permission(data):
            try:
                instance = self.get_object()
            except Http404:
                instance = None
            finally:
                if not instance or not instance.description:
                    instance = self.create_or_update_objective_description(
                        get_channel_name(request),
                        data,
                        key
                    )

            # For security reason, do not give access to local file address
            # Restrain data to some fields
            serializer = self.get_serializer(instance, fields=('owner'))
            data.update(serializer.data)

        replace_storage_addresses(request, data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(request, key)
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
                data = client.query_objectives()
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        query_params = request.query_params.get('search')
        if query_params is not None:
            try:
                data = filter_list(
                    object_type='objective',
                    data=data,
                    query_params=query_params)
            except OrcError as rpc_error:
                return Response({'message': rpc_error.details}, status=rpc_error.http_status())
            except Exception as e:
                logger.exception(e)
                return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        for objective in data:
            replace_storage_addresses(request, objective)

        return self.paginate_response(data)

    @action(detail=True, methods=['GET'])
    def leaderboard(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        validate_key(key)
        sort = request.query_params.get('sort', 'desc')

        try:
            validate_sort(sort)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with get_orchestrator_client(get_channel_name(request)) as client:
                leaderboard = client.query_objective_leaderboard(key, sort)
        except OrcError as rpc_error:
            return Response({'message': rpc_error.details}, status=rpc_error.http_status())
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(leaderboard, status=status.HTTP_200_OK)


class ObjectivePermissionViewSet(PermissionMixin,
                                 GenericViewSet):
    queryset = Objective.objects.all()
    serializer_class = ObjectiveSerializer

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions
    @action(detail=True, url_path='description', url_name='description')
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, 'query_objective', 'description')

    @action(detail=True)
    def metrics(self, request, *args, **kwargs):
        return self.download_file(request, 'query_objective', 'metrics')
