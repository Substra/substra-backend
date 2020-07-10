from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerTrainTupleSerializer
from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError, LedgerConflict
from substrapp.views.filters_utils import filter_list
from substrapp.views.utils import validate_pk, get_success_create_code, LedgerException


class TrainTupleViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        GenericViewSet):
    serializer_class = LedgerTrainTupleSerializer
    ledger_query_call = 'queryTraintuple'

    def get_queryset(self):
        return []

    def perform_create(self, serializer):
        return serializer.save()

    def commit(self, serializer, pkhash):
        # create on ledger
        try:
            data = serializer.create('mychannel', serializer.validated_data)
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
            'in_models_keys': request.data.get('in_models_keys'),
            # list of train data keys (which are stored in the train worker node)
            'train_data_sample_keys': request.data.get('train_data_sample_keys'),
            'tag': request.data.get('tag', ''),
            'metadata': request.data.get('metadata')
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Get traintuple pkhash to handle 408 timeout in invoke_ledger
        args = serializer.get_args(serializer.validated_data)

        try:
            data = query_ledger('mychannel', fcn='createTraintuple', args=args)
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
            data = query_ledger('mychannel', fcn='queryTraintuples', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        traintuple_list = [data]

        query_params = request.query_params.get('search', None)
        if query_params is not None:
            try:
                traintuple_list = filter_list(
                    object_type='traintuple',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        return Response(traintuple_list, status=status.HTTP_200_OK)

    def _retrieve(self, pk):
        validate_pk(pk)
        return get_object_from_ledger('mychannel', pk, self.ledger_query_call)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(pk)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)
