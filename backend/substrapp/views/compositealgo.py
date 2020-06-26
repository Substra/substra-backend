import tempfile

from django.http import Http404
from django.urls import reverse
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.models import CompositeAlgo
from substrapp.serializers import LedgerCompositeAlgoSerializer, CompositeAlgoSerializer
from substrapp.utils import get_hash
from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError, LedgerTimeout, LedgerConflict
from substrapp.views.utils import (PermissionMixin, find_primary_key_error,
                                   validate_pk, get_success_create_code, LedgerException, ValidationException,
                                   get_remote_asset, node_has_process_permission)
from substrapp.views.filters_utils import filter_list


def replace_storage_addresses(request, composite_algo):
    composite_algo['description']['storageAddress'] = request.build_absolute_uri(
        reverse('substrapp:composite_algo-description', args=[composite_algo['key']]))
    composite_algo['content']['storageAddress'] = request.build_absolute_uri(
        reverse('substrapp:composite_algo-file', args=[composite_algo['key']])
    )


class CompositeAlgoViewSet(mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    queryset = CompositeAlgo.objects.all()
    serializer_class = CompositeAlgoSerializer
    ledger_query_call = 'queryCompositeAlgo'

    def perform_create(self, serializer):
        return serializer.save()

    def commit(self, serializer, request):
        # create on db
        instance = self.perform_create(serializer)

        ledger_data = {
            'name': request.data.get('name'),
            'permissions': request.data.get('permissions'),
        }

        # init ledger serializer
        ledger_data.update({'instance': instance})
        ledger_serializer = LedgerCompositeAlgoSerializer(data=ledger_data,
                                                          context={'request': request})
        if not ledger_serializer.is_valid():
            # delete instance
            instance.delete()
            raise ValidationError(ledger_serializer.errors)

        # create on ledger
        try:
            data = ledger_serializer.create(ledger_serializer.validated_data)
        except LedgerTimeout as e:
            if isinstance(serializer.data, list):
                pkhash = [x['pkhash'] for x in serializer.data]
            else:
                pkhash = [serializer.data['pkhash']]
            data = {'pkhash': pkhash, 'validated': False}
            raise LedgerException(data, e.status)
        except LedgerConflict as e:
            raise ValidationException(e.msg, e.pkhash, e.status)
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

        pkhash = get_hash(file)
        serializer = self.get_serializer(data={
            'pkhash': pkhash,
            'file': file,
            'description': request.data.get('description')
        })

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            st = status.HTTP_400_BAD_REQUEST
            if find_primary_key_error(e):
                st = status.HTTP_409_CONFLICT
            raise ValidationException(e.args, pkhash, st)
        else:
            # create on ledger + db
            return self.commit(serializer, request)

    def create(self, request, *args, **kwargs):
        file = request.data.get('file')

        try:
            data = self._create(request, file)
        except ValidationException as e:
            return Response({'message': e.data, 'pkhash': e.pkhash}, status=e.st)
        except LedgerException as e:
            return Response({'message': e.data}, status=e.st)
        else:
            headers = self.get_success_headers(data)
            st = get_success_create_code()
            return Response(data, status=st, headers=headers)

    def create_or_update_composite_algo(self, composite_algo, pk):
        # get Compositealgo description from remote node
        url = composite_algo['description']['storageAddress']

        content = get_remote_asset(url, composite_algo['owner'], composite_algo['description']['hash'])

        f = tempfile.TemporaryFile()
        f.write(content)

        # save/update objective in local db for later use
        instance, created = CompositeAlgo.objects.update_or_create(pkhash=pk, validated=True)
        instance.description.save('description.md', f)

        return instance

    def _retrieve(self, request, pk):
        validate_pk(pk)
        data = get_object_from_ledger(pk, self.ledger_query_call)

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
                    instance = self.create_or_update_composite_algo(data, pk)

                # For security reason, do not give access to local file address
                # Restrain data to some fields
                # TODO: do we need to send creation date and/or last modified date ?
                serializer = self.get_serializer(instance, fields=('owner', 'pkhash'))
                data.update(serializer.data)

        replace_storage_addresses(request, data)

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(request, pk)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(fcn='queryCompositeAlgos', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        composite_algos_list = [data]

        # parse filters
        query_params = request.query_params.get('search', None)
        if query_params is not None:
            try:
                composite_algos_list = filter_list(
                    object_type='composite_algo',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        for group in composite_algos_list:
            for composite_algo in group:
                replace_storage_addresses(request, composite_algo)

        return Response(composite_algos_list, status=status.HTTP_200_OK)


class CompositeAlgoPermissionViewSet(PermissionMixin,
                                     GenericViewSet):
    queryset = CompositeAlgo.objects.all()
    serializer_class = CompositeAlgoSerializer
    ledger_query_call = 'queryCompositeAlgo'

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
