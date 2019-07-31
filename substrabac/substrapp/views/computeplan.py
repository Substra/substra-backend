from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerComputePlanSerializer
from substrapp.ledger_utils import query_ledger, LedgerError
from substrapp.views.utils import get_success_create_code


class ComputePlanViewSet(mixins.CreateModelMixin,
                         GenericViewSet):

    serializer_class = LedgerComputePlanSerializer

    def create(self, request, *args, **kwargs):
        # rely on serializer to parse and validate request data
        serializer = self.get_serializer(data=dict(request.data))
        serializer.is_valid(raise_exception=True)

        # get fltask to handle 408 timeout in next invoke ledger request
        args = serializer.get_args(serializer.validated_data)
        try:
            ledger_response = query_ledger(fcn='createComputePlan', args=args)
        except LedgerError as e:
            error = {'message': str(e.msg)}
            return Response(error, status=e.status)

        # create compute plan in ledger
        fltask = ledger_response.get('fltask')
        try:
            data = serializer.create(serializer.validated_data)
        except LedgerError as e:
            error = {'message': str(e.msg), 'fltask': fltask}
            return Response(error, status=e.status)

        # send successful response
        headers = self.get_success_headers(data)
        status = get_success_create_code()
        return Response(data, status=status, headers=headers)
