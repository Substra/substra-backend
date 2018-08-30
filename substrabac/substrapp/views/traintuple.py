from rest_framework import status, mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.conf import conf

from substrapp.models import Challenge
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
         -d "challenge_key=eb0295d98f37ae9e95102afae792d540137be2dedf6c4b00570ab1d1f355d033&algo_key=082f972d09049fdb7e34659f6fea82c5082be717cc9dab89bb92f620e6517106&model_key=082f972d09049fdb7e34659f6fea82c5082be717cc9dab89bb92f620e6517106&train_data_keys[]=aa1bb7c31f62244c0f3a761cc168804227115793d01c270021fe3f7935482dcc&train_data[]=aa2bb7c31f62244c0f3a761cc168804227115793d01c270021fe3f7935482dcc"
          -X POST http://localhost:8000/traintuple/

        or

        curl -H "Accept: text/html;version=0.0, */*;version=0.0" -H "Content-Type: application/json"
        -d '{"challenge_key":"eb0295d98f37ae9e95102afae792d540137be2dedf6c4b00570ab1d1f355d033","algo_key":"082f972d09049fdb7e34659f6fea82c5082be717cc9dab89bb92f620e6517106","model_key":"082f972d09049fdb7e34659f6fea82c5082be717cc9dab89bb92f620e6517106","train_data_keys":["aa1bb7c31f62244c0f3a761cc168804227115793d01c270021fe3f7935482dcc","aa2bb7c31f62244c0f3a761cc168804227115793d01c270021fe3f7935482dcc"]}'
         -X POST http://localhost:8000/traintuple/?format=json

        :param request:
        :return:
        '''

        data = request.data

        challenge_key = request.data.get('challenge_key', request.POST.get('challenge_key', None))
        # get pkhash of challenge from name
        try:
            challenge = Challenge.objects.get(pkhash=challenge_key)
        except:
            return Response({'message': 'This Challenge pkhash does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:

            algo_key = request.data.get('algo_key', request.POST.get('algo_key', None))
            model_key = request.data.get('model_key', request.POST.get('startModel_key', None))
            try:
                train_data_keys = request.data.getlist('train_data_keys', [])
            except:
                train_data_keys = request.data.get('train_data_keys', request.POST.getlist('train_data_keys', []))


            data = {
                'challenge_key': challenge.pkhash,
                'algo_key': algo_key,
                'model_key': model_key,
                'train_data_keys': train_data_keys,  # list of train data keys (which are stored in the train worker node)
            }

            # init ledger serializer
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            # create on ledger
            data = serializer.create(serializer.validated_data)

            st = status.HTTP_201_CREATED
            headers = self.get_success_headers(serializer.data)

            data.update(serializer.data)
            return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        # can modify result by interrogating `request.version`

        # using chu-nantes as in our testing owkin has been revoked
        org = conf['orgs']['chu-nantes']
        peer = org['peers'][0]

        data, st = queryLedger({
            'org': org,
            'peer': peer,
            'args': '{"Args":["queryTraintuples"]}'
        })

        return Response(data, status=st)
