from celery.result import AsyncResult
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class TaskViewSet(ViewSet):

    # https://stackoverflow.com/questions/9034091/how-to-check-task-status-in-celery
    def retrieve(self, request, pk=None):

        res = AsyncResult(pk)

        data = {
            'status': res.status
        }

        if not res.successful():
            if res.status == 'PENDING':
                data['message'] = 'Task is either waiting, ' \
                                  'does not exist in this context or has been removed after 24h'
            else:
                data['message'] = res.traceback
        else:
            data['result'] = res.result

        return Response(data, status=status.HTTP_200_OK)
