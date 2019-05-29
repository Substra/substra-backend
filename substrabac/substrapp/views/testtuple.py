from django.http import Http404
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerTestTupleSerializer
from substrapp.ledger_utils import queryLedger, getObjectFromLedger
from substrapp.utils import JsonException


class TestTupleViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       GenericViewSet):
    serializer_class = LedgerTestTupleSerializer
    ledger_query_call = 'queryTesttuple'

    def get_queryset(self):
        queryset = []
        return queryset

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        traintuple_key = request.data.get('traintuple_key', request.POST.get('traintuple_key', None))
        data_manager_key = request.data.get('data_manager_key', request.POST.get('data_manager_key', ''))
        tag = request.data.get('tag', request.POST.get('tag', ''))

        try:
            test_data_sample_keys = request.data.getlist('test_data_sample_keys', [])
        except Exception:
            test_data_sample_keys = request.data.get('test_data_sample_keys',
                                                     request.POST.getlist('test_data_sample_keys', []))

        data = {
            'traintuple_key': traintuple_key,
            'data_manager_key': data_manager_key,
            'test_data_sample_keys': test_data_sample_keys,  # list of test data keys
            'tag': tag
        }

        # init ledger serializer
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Get testtuple pkhash of the proposal with a queryLedger in case of 408 timeout
        args = serializer.get_args(serializer.validated_data)
        data, st = queryLedger(fcn='createTesttuple', args=args)

        if st == status.HTTP_200_OK:
            pkhash = data.get('key', data.get('keys'))
        else:
            # If queryLedger fails, invoke will fail too so we handle the issue right now
            if 'tkey' in data['message']:
                pkhash = data['message'].replace('(', '').replace(')', '').split('tkey: ')[-1].strip()

                if len(pkhash) != 64:
                    raise Exception('bad pkhash')
                else:
                    st = status.HTTP_409_CONFLICT

            return Response({'message': data['message'],
                             'pkhash': pkhash}, status=st)

        # create on ledger
        data, st = serializer.create(serializer.validated_data)

        if st == status.HTTP_408_REQUEST_TIMEOUT:
            return Response({'message': data['message'],
                             'pkhash': pkhash}, status=st)

        if st not in (status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED):
            if 'tkey' in data['message']:
                pkhash = data['message'].replace('(', '').replace(')', '').split('tkey: ')[-1].strip()

                if len(pkhash) != 64:
                    raise Exception('bad pkhash')
                else:
                    st = status.HTTP_409_CONFLICT

            return Response({'message': data['message'],
                             'pkhash': pkhash}, status=st)

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        # can modify result by interrogating `request.version`

        data, st = queryLedger(fcn='queryTesttuples', args=[])

        data = data if data else []

        return Response(data, status=st)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        if len(pk) != 64:
            return Response({'message': f'Wrong pk {pk}'}, status.HTTP_400_BAD_REQUEST)

        try:
            int(pk, 16)  # test if pk is correct (hexadecimal)
        except Exception:
            return Response({'message': f'Wrong pk {pk}'}, status.HTTP_400_BAD_REQUEST)
        else:
            # get instance from remote node
            try:
                data = getObjectFromLedger(pk, self.ledger_query_call)
            except JsonException as e:
                return Response(e.msg, status=status.HTTP_400_BAD_REQUEST)
            except Http404:
                return Response(f'No element with key {pk}', status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(data, status=status.HTTP_200_OK)
