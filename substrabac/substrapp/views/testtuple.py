import hashlib

from django.conf import settings
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


from substrapp.serializers import LedgerTestTupleSerializer
from substrapp.utils import queryLedger
from substrapp.views.utils import getObjectFromLedger, JsonException


class TestTupleViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       GenericViewSet):
    serializer_class = LedgerTestTupleSerializer

    def get_queryset(self):
        queryset = []
        return queryset

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        # TODO update
        '''
        curl -H "Accept: text/html;version=0.0, */*;version=0.0"
             -d "algo_key=da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b&model_key=10060f1d9e450d98bb5892190860eee8dd48594f00e0e1c9374a27c5acdba568&train_data_keys[]=62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a&train_data[]=42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"
             -X POST http://localhost:8001/traintuple/

        or

        curl -H "Accept: text/html;version=0.0, */*;version=0.0"
             -H "Content-Type: application/json"
             -d '{"algo_key":"da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b","model_key":"10060f1d9e450d98bb5892190860eee8dd48594f00e0e1c9374a27c5acdba568","train_data_keys":["62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a","42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"]}'
             -X POST http://localhost:8001/traintuple/?format=json

        :param request:
        :return:
        '''

        traintuple_key = request.data.get('traintuple_key', request.POST.get('traintuple_key', None))
        data_manager_key = request.data.get('data_manager_key', request.POST.get('data_manager_key', None))

        try:
            test_data_sample_keys = request.data.getlist('test_data_sample_keys', [])
        except:
            test_data_sample_keys = request.data.get('test_data_sample_keys', request.POST.getlist('test_data_sample_keys', []))

        data = {
            'traintuple_key': traintuple_key,
            'data_manager_key': data_manager_key,
            'test_data_sample_keys': test_data_sample_keys,  # list of test data keys
        }

        # init ledger serializer
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        # create on ledger
        data, st = serializer.create(serializer.validated_data)

        if st == status.HTTP_408_REQUEST_TIMEOUT:
            # with open(settings.LEDGER['signcert'], 'rb') as f:
            #     sha256_creator_hash = hashlib.sha256(f.read())

            #creator = sha256_creator_hash.hexdigest()
            sha256_pkhash = hashlib.sha256(('testtuple' + traintuple_key + data_manager_key).encode())
            pkhash = sha256_pkhash.hexdigest()
            return Response({'message': data['message'],
                             'pkhash': pkhash}, status=st)

        if st not in (status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED):
            try:
                pkhash = data['message'].replace('"', '').split('-')[
                    -1].strip()

                if not len(pkhash) == 64:
                    raise Exception('bad pkhash')

                return Response({'message': data['message'],
                                 'pkhash': pkhash}, status=st)
            except:
                return Response(data, status=st)

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        # can modify result by interrogating `request.version`

        data, st = queryLedger({
            'args': '{"Args":["queryTesttuples"]}'
        })

        return Response(data, status=st)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        if len(pk) != 64:
            return Response({'message': f'Wrong pk {pk}'}, status.HTTP_400_BAD_REQUEST)

        try:
            int(pk, 16)  # test if pk is correct (hexadecimal)
        except:
            return Response({'message': f'Wrong pk {pk}'}, status.HTTP_400_BAD_REQUEST)
        else:
            # get instance from remote node
            try:
                data = getObjectFromLedger(pk, 'queryTesttuple')
            except JsonException as e:
                return Response(e.msg, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(data, status=status.HTTP_200_OK)
