from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action

from substrapp.serializers import LedgerComputePlanSerializer
from substrapp.ledger_utils import invoke_ledger, query_ledger, LedgerError, get_object_from_ledger, LedgerConflict
from substrapp.views.utils import get_success_create_code, validate_pk
from substrapp.views.filters_utils import filter_list


class ComputePlanViewSet(mixins.CreateModelMixin,
                         GenericViewSet):

    serializer_class = LedgerComputePlanSerializer

    def get_queryset(self):
        return []

    def create(self, request, *args, **kwargs):
        # rely on serializer to parse and validate request data
        serializer = self.get_serializer(data=dict(request.data))
        serializer.is_valid(raise_exception=True)

        # get compute_plan_id to handle 408 timeout in next invoke ledger request
        args = serializer.get_args(serializer.validated_data)
        try:
            ledger_response = query_ledger('mychannel', fcn='createComputePlan', args=args)
        except LedgerConflict as e:
            error = {'message': str(e.msg), 'pkhash': e.pkhash}
            return Response(error, status=e.status)
        except LedgerError as e:
            error = {'message': str(e.msg)}
            return Response(error, status=e.status)

        # create compute plan in ledger
        compute_plan_id = ledger_response.get('computePlanID')
        try:
            data = serializer.create('mychannel', serializer.validated_data)
        except LedgerError as e:
            error = {'message': str(e.msg), 'computePlanID': compute_plan_id}
            return Response(error, status=e.status)

        # send successful response
        headers = self.get_success_headers(data)
        status = get_success_create_code()
        return Response(data, status=status, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            validate_pk(pk)
            data = get_object_from_ledger('mychannel', pk, 'queryComputePlan')
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger('mychannel', fcn='queryComputePlans', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        compute_plan_list = [data] if data else [[]]

        query_params = request.query_params.get('search', None)
        if query_params is not None:
            try:
                compute_plan_list = filter_list(
                    object_type='compute_plan',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        return Response(compute_plan_list, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def cancel(self, request, pk):
        validate_pk(pk)

        try:
            compute_plan = invoke_ledger('mychannel', fcn='cancelComputePlan', args={'key': pk}, only_pkhash=False)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        return Response(compute_plan, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def update_ledger(self, request, pk):
        validate_pk(pk)

        compute_plan_id = pk

        serializer = self.get_serializer(data=dict(request.data))
        serializer.is_valid(raise_exception=True)

        # update compute plan in ledger
        try:
            data = serializer.update('mychannel', compute_plan_id, serializer.validated_data)
        except LedgerError as e:
            error = {'message': str(e.msg), 'computePlanID': compute_plan_id}
            return Response(error, status=e.status)

        # send successful response
        headers = self.get_success_headers(data)
        status = get_success_create_code()
        return Response(data, status=status, headers=headers)
