from rest_framework import status, mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.models import Problem
from substrapp.serializers import ProblemSerializer, LedgerProblemSerializer

"""List all problems saved on local storage or submit a new one"""


class ProblemViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     GenericViewSet):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer

    # permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        """
        Create a new Problem \n
            TODO add info about what has to be posted\n
        - Example with curl (on localhost): \n
            curl -u username:password -H "Content-Type: application/json"\
            -X POST\
            -d '{"name": "tough problem", "test_data":
            ["data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b379",
            "data_5c1d9cd1c2c1082dde0921b56d11030c81f62fbb51932758b58ac2569dd0b389"],\
                "files": {"description.md": '#My tough problem',\
                'metrics.py': 'def AUC_score(y_true, y_pred):\n\treturn 1'}}'\
                http://127.0.0.1:8000/substrapp/problem/ \n
            Use double quotes for the json, simple quotes don't work.\n
        - Example with the python package requests (on localhost): \n
            requests.post('http://127.0.0.1:8000/runapp/rawdata/',\
                          auth=('username', 'password'),\
                          json={'name': 'tough problem', 'test_data': '??',\
                        'files': {'iris.csv': 'bla', 'specific.py': 'bli'}})\n
        ---
        response_serializer: ProblemSerializer
        """

        data = request.data
        problem_serializer = self.get_serializer(data={'metrics': data['metrics'],
                                                       'description': data['description']})
        problem_serializer.is_valid(raise_exception=True)
        problem = self.perform_create(problem_serializer)

        ledger_serializer = LedgerProblemSerializer(data={'test_data': data.getlist('test_data'),
                                                          'name': data['name'],
                                                          'problem_pkhash': problem.pkhash})
        ledger_serializer.is_valid(raise_exception=True)
        ledger_serializer.create(ledger_serializer.validated_data)

        headers = self.get_success_headers(problem_serializer.data)
        return Response(problem_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
