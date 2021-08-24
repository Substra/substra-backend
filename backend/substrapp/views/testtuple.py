import uuid

from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerTestTupleSerializer
from substrapp.ledger.api import query_ledger, get_object_from_ledger
from substrapp.ledger.exceptions import LedgerError
from substrapp.views.filters_utils import filter_list
from substrapp.views.utils import (validate_key, get_success_create_code, LedgerExceptionError, get_channel_name)
from libs.pagination import DefaultPageNumberPagination, PaginationMixin


class TestTupleViewSet(mixins.CreateModelMixin,
                       PaginationMixin,
                       GenericViewSet):
    serializer_class = LedgerTestTupleSerializer
    ledger_query_call = 'queryTesttuple'
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return []

    def perform_create(self, serializer):
        return serializer.save()

    def commit(self, serializer, channel_name):
        # create on ledger
        try:
            data = serializer.create(channel_name, serializer.validated_data)
        except LedgerError as e:
            raise LedgerExceptionError({'message': str(e.msg)}, e.status)
        else:
            return data

    def _create(self, request):
        key = uuid.uuid4()
        data = {
            'key': key,
            'objective_key': request.data.get('objective_key'),
            'traintuple_key': request.data.get('traintuple_key'),
            'data_manager_key': request.data.get('data_manager_key'),
            'test_data_sample_keys': request.data.get('test_data_sample_keys'),
            'tag': request.data.get('tag', ''),
            'metadata': request.data.get('metadata')
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        return self.commit(serializer, get_channel_name(request))

    def create(self, request, *args, **kwargs):
        try:
            data = self._create(request)
        except LedgerExceptionError as e:
            return Response(e.data, status=e.st)
        else:
            headers = self.get_success_headers(data)
            st = get_success_create_code()
            return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(get_channel_name(request), fcn='queryTesttuples', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        query_params = request.query_params.get('search')
        if query_params is not None:
            try:
                data = filter_list(
                    channel_name=get_channel_name(request),
                    object_type='testtuple',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        return self.paginate_response(data)

    def _retrieve(self, channel_name, key):
        validate_key(key)
        return get_object_from_ledger(channel_name, key, self.ledger_query_call)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(get_channel_name(request), key)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)
