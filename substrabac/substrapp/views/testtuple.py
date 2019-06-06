from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerTestTupleSerializer
from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError, LedgerConflict
from substrapp.views.utils import validate_pk, get_success_create_code


class TestTupleViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       GenericViewSet):
    serializer_class = LedgerTestTupleSerializer
    ledger_query_call = 'queryTesttuple'

    def get_queryset(self):
        return []

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = {
            'traintuple_key': request.data.get('traintuple_key'),
            'data_manager_key': request.data.get('data_manager_key', ''),
            'test_data_sample_keys': request.data.getlist('test_data_sample_keys'),
            'tag': request.data.get('tag', '')
        }

        # init ledger serializer
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Get testtuple pkhash to handle 408 timeout in invoke_ledger
        args = serializer.get_args(serializer.validated_data)

        try:
            data = query_ledger(fcn='createTesttuple', args=args)
        except LedgerConflict as e:
            return Response({'message': str(e), 'pkhash': e.pkhash}, status=e.status)
        except LedgerError as e:
            return Response({'message': str(e)}, status=e.status)

        pkhash = data.get('key')

        # create on ledger
        try:
            data = serializer.create(serializer.validated_data)
        except LedgerError as e:
            return Response({'message': str(e), 'pkhash': pkhash}, status=e.status)

        st = get_success_create_code()

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(fcn='queryTesttuples', args=[])
        except LedgerError as e:
            return Response({'message': str(e)}, status=e.status)

        data = data if data else []
        return Response(data, status=status.HTTP_200_OK)

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
            return Response({'message': str(e)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)
