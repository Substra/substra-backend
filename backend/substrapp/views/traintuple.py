from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerTrainTupleSerializer
from substrapp.ledger.api import query_ledger, get_object_from_ledger
from substrapp.ledger.exceptions import LedgerError
from substrapp.utils import new_uuid
from substrapp.views.filters_utils import filter_list
from substrapp.views.utils import (validate_pk, get_success_create_code, LedgerException, get_channel_name,
                                   data_to_data_response)


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

    def commit(self, serializer, channel_name):
        # create on ledger
        try:
            data = serializer.create(channel_name, serializer.validated_data)
        except LedgerError as e:
            raise LedgerException({'message': str(e.msg)}, e.status)
        else:
            return data

    def _create(self, request):
        pkhash = new_uuid()
        data = {
            'key': pkhash,
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
            data = query_ledger(get_channel_name(request), fcn='createTraintuple', args=args)
        except LedgerError as e:
            raise LedgerException({'message': str(e.msg)}, e.status)
        else:
            return self.commit(serializer, get_channel_name(request))

    def create(self, request, *args, **kwargs):
        try:
            data = self._create(request)
        except LedgerException as e:
            return Response(e.data, status=e.st)
        else:
            headers = self.get_success_headers(data)
            st = get_success_create_code()
            # Transform data to a data_response with only key
            data_response = data_to_data_response(data)
            return Response(data_response, status=st, headers=headers)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(get_channel_name(request), fcn='queryTraintuples', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        query_params = request.query_params.get('search', None)
        if query_params is not None:
            try:
                data = filter_list(
                    channel_name=get_channel_name(request),
                    object_type='traintuple',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)

        return Response(data, status=status.HTTP_200_OK)

    def _retrieve(self, channel_name, pk):
        validate_pk(pk)
        return get_object_from_ledger(channel_name, pk, self.ledger_query_call)

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(get_channel_name(request), pk)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            return Response(data, status=status.HTTP_200_OK)
