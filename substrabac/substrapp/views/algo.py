import tempfile
import logging

from django.http import Http404
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.models import Algo
from substrapp.serializers import LedgerAlgoSerializer, AlgoSerializer
from substrapp.utils import get_hash, get_from_node
from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError
from substrapp.views.utils import (ComputeHashMixin, ManageFileMixin, find_primary_key_error,
                                   validate_pk, get_success_create_code)
from substrapp.views.filters_utils import filter_list


class AlgoViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  ComputeHashMixin,
                  ManageFileMixin,
                  GenericViewSet):
    queryset = Algo.objects.all()
    serializer_class = AlgoSerializer
    ledger_query_call = 'queryAlgo'

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):

        file = request.data.get('file')
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
            return Response({'message': e.args, 'pkhash': pkhash}, status=st)

        # create on db
        try:
            instance = self.perform_create(serializer)
        except Exception as e:
            return Response({'message': e.args},
                            status=status.HTTP_400_BAD_REQUEST)

        # init ledger serializer
        ledger_serializer = LedgerAlgoSerializer(data={
            'name': request.data.get('name'),
            'permissions': request.data.get('permissions', 'all'),
            'instance': instance
        }, context={'request': request})
        if not ledger_serializer.is_valid():
            # delete instance
            instance.delete()
            raise ValidationError(ledger_serializer.errors)

        # create on ledger
        try:
            data = ledger_serializer.create(ledger_serializer.validated_data)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        st = get_success_create_code()
        headers = self.get_success_headers(serializer.data)
        d = dict(serializer.data)
        d.update(data)

        return Response(d, status=st, headers=headers)

    def create_or_update_algo(self, algo, pk):
        # get algo description from remote node
        url = algo['description']['storageAddress']

        response = get_from_node(url)

        try:
            computed_hash = self.compute_hash(response.content)
        except Exception as e:
            raise Exception('Failed to fetch description file') from e

        if computed_hash != algo['description']['hash']:
            msg = 'computed hash is not the same as the hosted file. ' \
                  'Please investigate for default of synchronization, corruption, or hacked'
            raise Exception(msg)

        f = tempfile.TemporaryFile()
        f.write(response.content)

        # save/update objective in local db for later use
        instance, created = Algo.objects.update_or_create(pkhash=pk, validated=True)
        instance.description.save('description.md', f)

        return instance

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            validate_pk(pk)
        except Exception as e:
            return Response({'message': str(e)}, status.HTTP_400_BAD_REQUEST)

        # get instance from remote node
        try:
            data = get_object_from_ledger(pk, self.ledger_query_call)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        # try to get it from local db to check if description exists
        try:
            instance = self.get_object()
        except Http404:
            instance = None

        # check if instance has description
        if not instance or not instance.description:
            try:
                instance = self.create_or_update_algo(data, pk)
            except Exception as e:
                logging.exception(e)
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        # For security reason, do not give access to local file address
        # Restrain data to some fields
        # TODO: do we need to send creation date and/or last modified date ?
        serializer = self.get_serializer(instance, fields=('owner', 'pkhash'))
        data.update(serializer.data)

        return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(fcn='queryAlgos', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        data = data if data else []

        algos_list = [data]

        # parse filters
        query_params = request.query_params.get('search', None)

        if query_params is not None:
            try:
                algos_list = filter_list(
                    object_type='algo',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)
            except Exception as e:
                logging.exception(e)
                return Response(
                    {'message': f'Malformed search filters {query_params}'},
                    status=status.HTTP_400_BAD_REQUEST)

        return Response(algos_list, status=status.HTTP_200_OK)

    @action(detail=True)
    def file(self, request, *args, **kwargs):
        return self.manage_file('file')

    @action(detail=True)
    def description(self, request, *args, **kwargs):
        return self.manage_file('description')
