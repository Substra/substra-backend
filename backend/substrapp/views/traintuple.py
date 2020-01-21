from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerTrainTupleSerializer
from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError
from substrapp.views.filters_utils import filter_list
from substrapp.views.utils import validate_pk, get_success_create_code
from substrapp import exceptions


class TrainTupleViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        GenericViewSet):
    serializer_class = LedgerTrainTupleSerializer

    def get_queryset(self):
        return []

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = {
            'algo_key': request.data.get('algo_key'),
            'data_manager_key': request.data.get('data_manager_key'),
            'rank': request.data.get('rank'),
            'compute_plan_id': request.data.get('compute_plan_id', ''),
            'in_models_keys': request.data.getlist('in_models_keys'),
            # list of train data keys (which are stored in the train worker node)
            'train_data_sample_keys': request.data.getlist('train_data_sample_keys'),
            'tag': request.data.get('tag', '')
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Get compositetraintuple key to handle timeout (408) in invoke_ledger
        args = serializer.get_args(serializer.validated_data)
        try:
            data = query_ledger(fcn='createTraintuple', args=args)
        except LedgerError as e:
            raise exceptions.from_ledger_error(e)
        key = data.get('key')

        try:
            data = serializer.create(serializer.validated_data)
        except LedgerError as e:
            raise exceptions.from_ledger_error(e, data={'key': key})

        headers = self.get_success_headers(data)
        st = get_success_create_code()
        return Response(data, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(fcn='queryTraintuples', args=[])
        except LedgerError as e:
            raise exceptions.from_ledger_error(e)

        traintuple_list = [data]

        query_params = request.query_params.get('search')
        if query_params:
            try:
                traintuple_list = filter_list(
                    object_type='traintuple',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                raise exceptions.from_ledger_error(e)

        return Response(traintuple_list, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        validate_pk(pk)

        try:
            data = get_object_from_ledger(pk, 'queryTraintuple')
        except LedgerError as e:
            raise exceptions.from_ledger_error(e)

        return Response(data, status=status.HTTP_200_OK)
