from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerTrainTupleSerializer
from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError, LedgerConflict
from substrapp.views.utils import validate_pk, get_success_create_code


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

    def create(self, request, *args, **kwargs):
        data = {
            'algo_key': request.data.get('algo_key'),
            'data_manager_key': request.data.get('data_manager_key'),
            'objective_key': request.data.get('objective_key'),
            'rank': request.data.get('rank'),
            'FLtask_key': request.data.get('FLtask_key', ''),
            'in_models_keys': request.data.getlist('in_models_keys'),
            # list of train data keys (which are stored in the train worker node)
            'train_data_sample_keys': request.data.getlist('train_data_sample_keys'),
            'tag': request.data.get('tag', '')
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Get traintuple pkhash to handle 408 timeout in invoke_ledger
        args = serializer.get_args(serializer.validated_data)

        try:
            data = query_ledger(fcn='createTraintuple', args=args)
        except LedgerConflict as e:
            return Response({'message': str(e.msg), 'pkhash': e.pkhash}, status=e.status)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        pkhash = data.get('key')

        # create on ledger
        try:
            data = serializer.create(serializer.validated_data)
        except LedgerError as e:
            return Response({'message': str(e.msg), 'pkhash': pkhash}, status=e.status)

        st = get_success_create_code()

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):

        try:
            data = query_ledger(fcn='queryTraintuples', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        data = data if data else []

        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            validate_pk(pk)
        except Exception as e:
            return Response({'message': str(e)}, status.HTTP_400_BAD_REQUEST)

        # get instance from remote node
        try:
            data = get_object_from_ledger(pk, self.ledger_query_call)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)
