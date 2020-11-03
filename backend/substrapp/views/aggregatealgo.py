import tempfile

from django.http import Http404
from django.urls import reverse
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.models import AggregateAlgo
from substrapp.serializers import LedgerAggregateAlgoSerializer, AggregateAlgoSerializer
from substrapp.utils import get_hash
from substrapp.ledger.api import query_ledger, get_object_from_ledger
from substrapp.ledger.exceptions import LedgerError, LedgerTimeout, LedgerConflict
from substrapp.views.utils import (PermissionMixin,
                                   validate_key, get_success_create_code, LedgerException, ValidationException,
                                   get_remote_asset, node_has_process_permission, get_channel_name)
from substrapp.views.filters_utils import filter_list


def replace_storage_addresses(request, aggregate_algo):
    aggregate_algo['description']['storage_address'] = request.build_absolute_uri(
        reverse('substrapp:aggregate_algo-description', args=[aggregate_algo['key']]))
    aggregate_algo['content']['storage_address'] = request.build_absolute_uri(
        reverse('substrapp:aggregate_algo-file', args=[aggregate_algo['key']])
    )


class AggregateAlgoViewSet(mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    queryset = AggregateAlgo.objects.all()
    serializer_class = AggregateAlgoSerializer
    ledger_query_call = 'queryAggregateAlgo'

    def perform_create(self, serializer):
        return serializer.save()

    def commit(self, serializer, request):
        # create on db
        instance = self.perform_create(serializer)

        ledger_data = {
            'name': request.data.get('name'),
            'permissions': request.data.get('permissions'),
            'metadata': request.data.get('metadata')
        }

        # init ledger serializer
        ledger_data.update({'instance': instance})
        ledger_serializer = LedgerAggregateAlgoSerializer(data=ledger_data,
                                                          context={'request': request})
        if not ledger_serializer.is_valid():
            # delete instance
            instance.delete()
            raise ValidationError(ledger_serializer.errors)

        # create on ledger
        try:
            data = ledger_serializer.create(get_channel_name(request), ledger_serializer.validated_data)
        except LedgerTimeout as e:
            if isinstance(serializer.data, list):
                key = [x['key'] for x in serializer.data]
            else:
                key = [serializer.data['key']]
            data = {'key': key, 'validated': False}
            raise LedgerException(data, e.status)
        except LedgerConflict as e:
            raise ValidationException(e.msg, e.key, e.status)
        except LedgerError as e:
            instance.delete()
            raise LedgerException(str(e.msg), e.status)
        except Exception:
            instance.delete()
            raise

        d = dict(serializer.data)
        d.update(data)

        return d

    def _create(self, request, file):

        checksum = get_hash(file)
        serializer = self.get_serializer(data={
            'file': file,
            'description': request.data.get('description'),
            'checksum': checksum
        })

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise ValidationException(e.args, '(not computed)', status.HTTP_400_BAD_REQUEST)
        else:
            # create on ledger + db
            return self.commit(serializer, request)

    def create(self, request, *args, **kwargs):
        file = request.data.get('file')

        try:
            data = self._create(request, file)
        except ValidationException as e:
            return Response({'message': e.data, 'key': e.key}, status=e.st)
        except LedgerException as e:
            return Response({'message': e.data}, status=e.st)
        else:
            headers = self.get_success_headers(data)
            st = get_success_create_code()
            return Response(data, status=st, headers=headers)

    def create_or_update_aggregate_algo(self, channel_name, aggregate_algo, key):
        # get Aggregatealgo description from remote node
        url = aggregate_algo['description']['storage_address']

        content = get_remote_asset(channel_name, url, aggregate_algo['owner'], aggregate_algo['description']['checksum'])

        f = tempfile.TemporaryFile()
        f.write(content)

        # save/update objective in local db for later use
        instance, created = AggregateAlgo.objects.update_or_create(key=key, validated=True)
        instance.description.save('description.md', f)

        return instance

    def _retrieve(self, request, key):
        validate_key(key)
        data = get_object_from_ledger(get_channel_name(request), key, self.ledger_query_call)

        # do not cache if node has not process permission
        if node_has_process_permission(data):
            # try to get it from local db to check if description exists
            try:
                instance = self.get_object()
            except Http404:
                instance = None
            finally:
                # check if instance has description
                if not instance or not instance.description:
                    instance = self.create_or_update_aggregate_algo(get_channel_name(request), data, key)

                # For security reason, do not give access to local file address
                # Restrain data to some fields
                # TODO: do we need to send creation date and/or last modified date ?
                serializer = self.get_serializer(instance, fields=('owner'))
                data.update(serializer.data)

        replace_storage_addresses(request, data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(request, key)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(get_channel_name(request), fcn='queryAggregateAlgos', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        # parse filters
        query_params = request.query_params.get('search')
        if query_params is not None:
            try:
                data = filter_list(
                    channel_name=get_channel_name(request),
                    object_type='aggregate_algo',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        for aggregate_algo in data:
            replace_storage_addresses(request, aggregate_algo)

        return Response(data, status=status.HTTP_200_OK)


class AggregateAlgoPermissionViewSet(PermissionMixin,
                                     GenericViewSet):
    queryset = AggregateAlgo.objects.all()
    serializer_class = AggregateAlgoSerializer
    ledger_query_call = 'queryAggregateAlgo'

    @action(detail=True)
    def file(self, request, *args, **kwargs):
        return self.download_file(request, 'file', 'content')

    # actions cannot be named "description"
    # https://github.com/encode/django-rest-framework/issues/6490
    # for some of the restricted names see:
    # https://www.django-rest-framework.org/api-guide/viewsets/#introspecting-viewset-actions
    @action(detail=True, url_path='description', url_name='description')
    def description_(self, request, *args, **kwargs):
        return self.download_file(request, 'description')
