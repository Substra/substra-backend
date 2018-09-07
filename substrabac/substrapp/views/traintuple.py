from django.conf import settings
from rest_framework import status, mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


from substrapp.serializers import LedgerTrainTupleSerializer
from substrapp.utils import queryLedger


class TrainTupleViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        GenericViewSet):
    serializer_class = LedgerTrainTupleSerializer

    def get_queryset(self):
        queryset = []
        return queryset

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        '''
        curl -H "Accept: text/html;version=0.0, */*;version=0.0"
             -d "algo_key=381310d64a0dbeb21272eb432b7a948d841bf7dc20514d00f901c16dec0463c3&model_key=10060f1d9e450d98bb5892190860eee8dd48594f00e0e1c9374a27c5acdba568&train_data_keys[]=62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a&train_data[]=42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"
             -X POST http://localhost:8001/traintuple/

        or

        curl -H "Accept: text/html;version=0.0, */*;version=0.0"
             -H "Content-Type: application/json"
             -d '{"algo_key":"381310d64a0dbeb21272eb432b7a948d841bf7dc20514d00f901c16dec0463c3","model_key":"10060f1d9e450d98bb5892190860eee8dd48594f00e0e1c9374a27c5acdba568","train_data_keys":["62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a","42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"]}'
             -X POST http://localhost:8001/traintuple/?format=json

        :param request:
        :return:
        '''

        algo_key = request.data.get('algo_key', request.POST.get('algo_key', None))
        model_key = request.data.get('model_key', request.POST.get('startModel_key', None))
        try:
            train_data_keys = request.data.getlist('train_data_keys', [])
        except:
            train_data_keys = request.data.get('train_data_keys', request.POST.getlist('train_data_keys', []))


        data = {
            'algo_key': algo_key,
            'model_key': model_key,
            'train_data_keys': train_data_keys,  # list of train data keys (which are stored in the train worker node)
        }

        # init ledger serializer
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        # create on ledger
        data = serializer.create(serializer.validated_data)

        st = status.HTTP_200_OK
        headers = self.get_success_headers(serializer.data)

        return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        # can modify result by interrogating `request.version`

        data, st = queryLedger({
            'org': settings.LEDGER['org'],
            'peer': settings.LEDGER['peer'],
            'args': '{"Args":["queryTraintuples"]}'
        })

        return Response(data, status=st)
