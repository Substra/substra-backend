from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from substrapp.models import Algo, Problem
from substrapp.serializers import LedgerAlgoSerializer, AlgoSerializer


class AlgoViewSet(ModelViewSet):
    queryset = Algo.objects.all()
    serializer_class = AlgoSerializer

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
            serializer = self.get_serializer(data={'algo': data['algo']})
            serializer.is_valid(raise_exception=True)

            # create on db
            instance = self.perform_create(serializer)

            # init ledger serializer
            ledger_serializer = LedgerAlgoSerializer(data={'name': data['name'],
                                                           'permissions': data.get('permissions', 'all'),
                                                           'problem': problem.pkhash,
                                                           'instance_pkhash': instance.pkhash})
            if not ledger_serializer.is_valid():
                # delete instance
                instance.delete()
                raise ValidationError(ledger_serializer.errors)

            # create on ledger
            ledger_serializer.create(serializer.validated_data)

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
