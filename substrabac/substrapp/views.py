from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from substrapp.models import Problem
from substrapp.serializers import ProblemSerializer, LedgerProblemSerializer


class ProblemList(APIView):
    """List all problems saved on local storage or submit a new one"""

    # permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        """
        List all problems stored in local Storage \n
        - Example with curl (on localhost): \n
        curl -u username:pwd GET http://127.0.0.1:8000/substrapp/problem/ \n
        - Example with the python package requests (on localhost): \n
        requests.get('http://127.0.0.1:8000/substrapp/problem/',\
            auth=('username', 'pwd'))\n
        ---
        response_serializer: ProblemSerializer
        """
        problems = Problem.objects.all()
        serializer = ProblemSerializer(problems, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
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
        print('data', request.data)
        print('files', request.FILES)
        problem_serializer = ProblemSerializer(data={'metrics': data['metrics'],
                                                'description':
                                                data['description']})
        ledger_serializer = LedgerProblemSerializer(data={'test_data':
                                                     data['test_data'],
                                                     'name': data['name']})
        if problem_serializer.is_valid():
            problem_serializer.save()
            # run smart contract to register problem in ledger
            # TODO using problem.pk as description hash
            # need to compute metrics hash
            # metrics_hash = compute_hash(problem.metrics)
            # print(metrics_hash)
            return Response(problem_serializer.validated_data, status=status.HTTP_201_CREATED)
        return Response(problem_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Create your views here.
