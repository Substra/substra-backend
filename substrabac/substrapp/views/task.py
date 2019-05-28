from celery.result import AsyncResult
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class TaskViewSet(ViewSet):

    # https://stackoverflow.com/questions/9034091/how-to-check-task-status-in-celery
    def retrieve(self, request, pk=None):

        res = AsyncResult(pk)

        try:
            data = {
                'status': res.status
            }
        except Exception:
            return Response({'message': 'Can\'t get task status'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if not res.successful():
                if res.status == 'PENDING':
                    data['message'] = 'Task is either waiting, ' \
                                      'does not exist in this context or has been removed after 24h'
                else:
                    data['message'] = res.traceback
            else:
                data['result'] = res.result

            return Response(data, status=status.HTTP_200_OK)
