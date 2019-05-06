import json
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerTrainTupleSerializer
from substrapp.utils import queryLedger
from substrapp.views.utils import JsonException


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
             -d "algo_key=da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b&model_key=10060f1d9e450d98bb5892190860eee8dd48594f00e0e1c9374a27c5acdba568&train_data_sample_keys[]=62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a&train_data[]=42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"
             -X POST http://localhost:8001/traintuple/

        or

        curl -H "Accept: text/html;version=0.0, */*;version=0.0"
             -H "Content-Type: application/json"
             -d '{"algo_key":"da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b","model_key":"10060f1d9e450d98bb5892190860eee8dd48594f00e0e1c9374a27c5acdba568","train_data_sample_keys":["62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a","42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"]}'
             -X POST http://localhost:8001/traintuple/?format=json

        :param request:
        :return:
        '''

        algo_key = request.data.get('algo_key', request.POST.get('algo_key', None))
        data_manager_key = request.data.get('data_manager_key', request.POST.get('data_manager_key', None))
        objective_key = request.data.get('objective_key', request.POST.get('objective_key', None))
        rank = request.data.get('rank', request.POST.get('rank', None))
        FLtask_key = request.data.get('FLtask_key', request.POST.get('FLtask_key', ''))
        tag = request.data.get('tag', request.POST.get('tag', ''))

        try:
            in_models_keys = request.data.getlist('in_models_keys', [])
        except:
            in_models_keys = request.data.get('in_models_keys', request.POST.getlist('in_models_keys', []))

        try:
            train_data_sample_keys = request.data.getlist('train_data_sample_keys', [])
        except:
            train_data_sample_keys = request.data.get('train_data_sample_keys', request.POST.getlist('train_data_sample_keys', []))

        data = {
            'algo_key': algo_key,
            'data_manager_key': data_manager_key,
            'objective_key': objective_key,
            'rank': rank,
            'FLtask_key': FLtask_key,
            'in_models_keys': in_models_keys,
            'train_data_sample_keys': train_data_sample_keys,  # list of train data keys (which are stored in the train worker node)
            'tag': tag
        }

        # init ledger serializer
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Get traintuple pkhash of the proposal with a queryLedger in case of 408 timeout
        args = serializer.get_args(serializer.validated_data)
        data, st = queryLedger({'args': '{"Args":["createTraintuple", ' + args + ']}'})
        if st == status.HTTP_200_OK:
            pkhash = data.get('key', data.get('keys'))
        else:
            # If queryLedger fails, invoke will fail too so we handle the issue right now
            try:
                data['message'] = data['message'].split('Error')[-1]
                msg = json.loads(data['message'].split('payload:')[-1].strip().strip('"').encode('utf-8').decode('unicode_escape'))
                pkhash = msg['error'].replace('(', '').replace(')', '').split('tkey: ')[-1].strip()

                if len(pkhash) != 64:
                    raise Exception('bad pkhash')
                else:
                    st = status.HTTP_409_CONFLICT

                return Response({'message': data['message'].split('payload')[0],
                                 'pkhash': pkhash}, status=st)
            except:
                return Response(data, status=st)

        # create on ledger
        data, st = serializer.create(serializer.validated_data)

        if st == status.HTTP_408_REQUEST_TIMEOUT:
            return Response({'message': data['message'],
                             'pkhash': pkhash}, status=st)

        if st not in (status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED):
            try:
                data['message'] = data['message'].split('Error')[-1]
                msg = json.loads(data['message'].split('payload:')[-1].strip().strip('"').encode('utf-8').decode('unicode_escape'))
                pkhash = msg['error'].replace('(', '').replace(')', '').split('tkey: ')[-1].strip()

                if len(pkhash) != 64:
                    raise Exception('bad pkhash')
                else:
                    st = status.HTTP_409_CONFLICT

                return Response({'message': data['message'].split('payload')[0],
                                 'pkhash': pkhash}, status=st)
            except:
                return Response(data, status=st)

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        data, st = queryLedger({
            'args': '{"Args":["queryTraintuples"]}'
        })

        data = data if data else []

        return Response(data, status=st)

    def getObjectFromLedger(self, pk):
        # get instance from remote node
        data, st = queryLedger({
            'args': f'{{"Args":["queryTraintuple","{pk}"]}}'
        })

        if st != status.HTTP_200_OK:
            raise JsonException(data)

        if 'permissions' not in data or data['permissions'] == 'all':
            return data
        else:
            raise Exception('Not Allowed')

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
                data = self.getObjectFromLedger(pk)
            except JsonException as e:
                return Response(e.msg, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(data, status=status.HTTP_200_OK)
