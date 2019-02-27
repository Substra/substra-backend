import hashlib

from django.conf import settings
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


from substrapp.serializers import LedgerTrainTupleSerializer
from substrapp.utils import queryLedger
from substrapp.views.utils import getObjectFromLedger, JsonException


class TrainTupleViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        GenericViewSet):
    serializer_class = LedgerTrainTupleSerializer

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

        algo_key = request.data.get('algo_key', request.POST.get('algo_key', None))
        dataset_key = request.data.get('dataset_key', request.POST.get('dataset_key', None))
        rank = request.data.get('rank', request.POST.get('rank', None))
        FLtask_key = request.data.get('FLtask_key', request.POST.get('FLtask_key', ''))

        try:
            input_models_keys = request.data.getlist('input_models_keys', [])
        except:
            input_models_keys = request.data.get('input_models_keys', request.POST.getlist('input_models_keys', []))

        try:
            train_data_keys = request.data.getlist('train_data_keys', [])
        except:
            train_data_keys = request.data.get('train_data_keys', request.POST.getlist('train_data_keys', []))

        data = {
            'algo_key': algo_key,
            'dataset_key': dataset_key,
            'rank': rank,
            'FLtask_key': FLtask_key,
            'input_models_keys': input_models_keys,
            'train_data_keys': train_data_keys,  # list of train data keys (which are stored in the train worker node)
        }

        # init ledger serializer
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        # create on ledger
        data, st = serializer.create(serializer.validated_data)

        if st == status.HTTP_408_REQUEST_TIMEOUT:
            with open(settings.LEDGER['signcert'], 'rb') as f:
                sha256_creator_hash = hashlib.sha256(f.read())

            creator = sha256_creator_hash.hexdigest()
            sha256_pkhash = hashlib.sha256((algo_key + ','.join(input_models_keys) + ','.join(train_data_keys) + creator).encode())
            pkhash = sha256_pkhash.hexdigest()
            return Response({'message': data['message'],
                             'pkhash': pkhash}, status=st)

        if st not in (status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED):
            try:
                pkhash = data['message'].replace('"', '').split('-')[-1].strip()

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
            'args': '{"Args":["queryTraintuples"]}'
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
                data = getObjectFromLedger(pk)
            except JsonException as e:
                return Response(e.msg, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(data, status=status.HTTP_200_OK)
