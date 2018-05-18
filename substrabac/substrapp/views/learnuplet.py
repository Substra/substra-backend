from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from substrapp.models import Problem
from substrapp.serializers import LedgerLearnupletSerializer


class LearnupletViewSet(ModelViewSet):
    serializer_class = LedgerLearnupletSerializer

    def get_queryset(self):
        queryset = []
        return queryset

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = request.data

        # get pkhash of problem from name
        try:
            problem = Problem.objects.get(pkhash=data['problem'])
        except:
            return Response({'message': 'This Problem pkhash does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:

            data = {
                'problem': problem.pkhash,
                'model': data.get('model'),
                'train_data': data.getlist('train_data'),  # list of train data keys (which are stored in the train worker node)
            }

            # init ledger serializer
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            # create on ledger
            serializer.create(serializer.validated_data)

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
