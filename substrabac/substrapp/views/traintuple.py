from rest_framework import status, mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.models import Challenge
from substrapp.serializers import LedgerTrainTupleSerializer


class TrainTupleViewSet(mixins.CreateModelMixin,
                        GenericViewSet):
    serializer_class = LedgerTrainTupleSerializer

    def get_queryset(self):
        queryset = []
        return queryset

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = request.data

        # get pkhash of challenge from name
        try:
            challenge = Challenge.objects.get(pkhash=data['challenge_key'])
        except:
            return Response({'message': 'This Challenge pkhash does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:

            data = {
                'challenge_key': challenge.pkhash,
                'algo_key': data.get('algo_key'),
                'model_key': data.get('model_key'),
                'train_data_keys': data.getlist('train_data_keys'),  # list of train data keys (which are stored in the train worker node)
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
