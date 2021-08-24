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
from libs.pagination import DefaultPageNumberPagination, PaginationMixin


def create_compute_plan(channel_name, data):
    # rely on serializer to parse and validate request data
    serializer = LedgerComputePlanSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    # create compute plan in ledger
    key = uuid.uuid4()
    return serializer.create(channel_name, key, serializer.validated_data)


class ComputePlanViewSet(mixins.CreateModelMixin,
                         PaginationMixin,
                         GenericViewSet):

    serializer_class = LedgerComputePlanSerializer
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return []

    def create(self, request, *args, **kwargs):
        try:
            data = create_compute_plan(get_channel_name(request), dict(request.data))
        except LedgerError as e:
            error = {'message': str(e.msg), 'key': data['key']}
            return Response(error, status=e.status)

        # send successful response
        headers = self.get_success_headers(data)
        status = get_success_create_code()
        return Response(data, status=status, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        validate_key(key)

        try:
            data = get_object_from_ledger(get_channel_name(request), key, 'queryComputePlan')
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

        return self.paginate_response(data)

    @action(detail=True, methods=['POST'])
    def cancel(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]
        validate_key(key)

        try:
            compute_plan = invoke_ledger(
                get_channel_name(request),
                fcn='cancelComputePlan',
                args={'key': key},
                only_key=False)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        return Response(compute_plan, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def update_ledger(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        key = self.kwargs[lookup_url_kwarg]

        validate_key(key)

        serializer = self.get_serializer(data=dict(request.data))
        serializer.is_valid(raise_exception=True)

        # update compute plan in ledger
        try:
            data = serializer.update(get_channel_name(request), key, serializer.validated_data)
        except LedgerError as e:
            error = {'message': str(e.msg), 'key': key}
            return Response(error, status=e.status)

        # send successful response
        headers = self.get_success_headers(data)
        status = get_success_create_code()
        return Response(data, status=status, headers=headers)


class GenericSubassetViewset(PaginationMixin,
                             GenericViewSet):

    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return []

    def list(self, request, compute_plan_pk, ledger_query_call, subasset_name):
        if not self.is_page_size_param_present():
            # We choose to force the page_size parameter in these views in order to limit the number of queries
            # to the chaincode
            return Response(status=status.HTTP_400_BAD_REQUEST, data='page_size param is required')

        validate_key(compute_plan_pk)
        channel_name = get_channel_name(request)

        try:
            compute_plan = get_object_from_ledger(channel_name, compute_plan_pk, 'queryComputePlan')
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        subasset_keys = compute_plan.get(f"{subasset_name}_keys", [])

        page_subasset_keys = self.paginate_queryset(subasset_keys)

        subasset_list = []

        # Use the get method from traintuple view
        for key in page_subasset_keys:
            try:
                asset = get_object_from_ledger(channel_name, key, f"{ledger_query_call}")
                subasset_list.append(asset)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        return self.get_paginated_response(subasset_list)


class CPTraintupleViewSet(GenericSubassetViewset):

    def list(self, request, compute_plan_pk):
        return super().list(
            request=request,
            compute_plan_pk=compute_plan_pk,
            ledger_query_call='queryTraintuple',
            subasset_name='traintuple')


class CPAggregatetupleViewSet(GenericSubassetViewset):
    def list(self, request, compute_plan_pk):
        return super().list(
            request=request,
            compute_plan_pk=compute_plan_pk,
            ledger_query_call='queryAggregatetuple',
            subasset_name='aggregatetuple')


class CPCompositeTraintupleViewSet(GenericSubassetViewset):

    def list(self, request, compute_plan_pk):
        return super().list(
            request=request,
            compute_plan_pk=compute_plan_pk,
            ledger_query_call='queryCompositeTraintuple',
            subasset_name='composite_traintuple')


class CPTesttupleViewSet(GenericSubassetViewset):

    def list(self, request, compute_plan_pk):
        return super().list(
            request=request,
            compute_plan_pk=compute_plan_pk,
            ledger_query_call='queryTesttuple',
            subasset_name='testtuple')
