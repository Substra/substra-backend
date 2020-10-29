import uuid

from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action

from substrapp.serializers import LedgerComputePlanSerializer
from substrapp.ledger.api import invoke_ledger, query_ledger, get_object_from_ledger
from substrapp.ledger.exceptions import LedgerError
from substrapp.views.utils import get_success_create_code, validate_key, get_channel_name
from substrapp.views.filters_utils import filter_list


def create_compute_plan(channel_name, data):
    # rely on serializer to parse and validate request data
    serializer = LedgerComputePlanSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    # create compute plan in ledger
    compute_plan_id = uuid.uuid4()
    return serializer.create(channel_name, compute_plan_id, serializer.validated_data)


class ComputePlanViewSet(mixins.CreateModelMixin,
                         GenericViewSet):

    serializer_class = LedgerComputePlanSerializer

    def get_queryset(self):
        return []

    def create(self, request, *args, **kwargs):
        try:
            data = create_compute_plan(get_channel_name(request), dict(request.data))
        except LedgerError as e:
            error = {'message': str(e.msg), 'compute_plan_id': data['compute_plan_id']}
            return Response(error, status=e.status)

        # send successful response
        headers = self.get_success_headers(data)
        status = get_success_create_code()
        return Response(data, status=status, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]
        validate_key(pk)

        try:
            data = get_object_from_ledger(get_channel_name(request), pk, 'queryComputePlan')
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(get_channel_name(request), fcn='queryComputePlans', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        data = data or []

        query_params = request.query_params.get('search')
        if query_params is not None:
            try:
                data = filter_list(
                    channel_name=get_channel_name(request),
                    object_type='compute_plan',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def cancel(self, request, pk):
        validate_key(pk)

        try:
            compute_plan = invoke_ledger(
                get_channel_name(request),
                fcn='cancelComputePlan',
                args={'key': pk},
                only_key=False)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        return Response(compute_plan, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def update_ledger(self, request, pk):

        validate_key(pk)

        compute_plan_id = pk

        serializer = self.get_serializer(data=dict(request.data))
        serializer.is_valid(raise_exception=True)

        # update compute plan in ledger
        try:
            data = serializer.update(get_channel_name(request), compute_plan_id, serializer.validated_data)
        except LedgerError as e:
            error = {'message': str(e.msg), 'compute_plan_id': compute_plan_id}
            return Response(error, status=e.status)

        # send successful response
        headers = self.get_success_headers(data)
        status = get_success_create_code()
        return Response(data, status=status, headers=headers)
