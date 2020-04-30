from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerCompositeTraintupleSerializer
from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError, LedgerConflict
from substrapp.views.filters_utils import filter_list
from substrapp.views.utils import validate_pk, get_success_create_code, LedgerException


class CompositeTraintupleViewSet(mixins.CreateModelMixin,
                                 mixins.RetrieveModelMixin,
                                 mixins.ListModelMixin,
                                 GenericViewSet):
    serializer_class = LedgerCompositeTraintupleSerializer
    ledger_query_call = 'queryCompositeTraintuple'

    def get_queryset(self):
        return []

    def perform_create(self, serializer):
        return serializer.save()

    def commit(self, serializer, pkhash):
        # create on ledger
        try:
            data = serializer.create(serializer.validated_data)
        except LedgerError as e:
            raise LedgerException({'message': str(e.msg), 'pkhash': pkhash}, e.status)
        else:
            return data

    def _create(self, request):
        data = {
            'algo_key': request.data.get('algo_key'),
            'data_manager_key': request.data.get('data_manager_key'),
            'rank': request.data.get('rank'),
            'compute_plan_id': request.data.get('compute_plan_id', ''),
            'in_head_model_key': request.data.get('in_head_model_key', ''),
            'in_trunk_model_key': request.data.get('in_trunk_model_key', ''),
            'out_trunk_model_permissions': request.data.get('out_trunk_model_permissions'),
            'train_data_sample_keys': request.data.get('train_data_sample_keys'),
            'tag': request.data.get('tag', '')
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Get compositetraintuple pkhash to handle 408 timeout in invoke_ledger
        args = serializer.get_args(serializer.validated_data)

        try:
            data = query_ledger(fcn='createCompositeTraintuple', args=args)
        except LedgerConflict as e:
            raise LedgerException({'message': str(e.msg), 'pkhash': e.pkhash}, e.status)
        except LedgerError as e:
            raise LedgerException({'message': str(e.msg)}, e.status)
        else:
            pkhash = data.get('key')
            return self.commit(serializer, pkhash)

    def create(self, request, *args, **kwargs):
        try:
            data = self._create(request)
        except LedgerException as e:
            return Response(e.data, status=e.st)
        else:
            headers = self.get_success_headers(data)
            st = get_success_create_code()
            return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(fcn='queryCompositeTraintuples', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        compositetraintuple_list = [data]

        query_params = request.query_params.get('search', None)
        if query_params is not None:
            try:
                compositetraintuple_list = filter_list(
                    object_type='composite_traintuple',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        return Response(compositetraintuple_list, status=status.HTTP_200_OK)

    def _retrieve(self, pk):
        validate_pk(pk)
        return get_object_from_ledger(pk, self.ledger_query_call)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(pk)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)
