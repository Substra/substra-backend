import uuid

from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerTrainTupleSerializer
from substrapp.ledger.api import query_ledger, get_object_from_ledger
from substrapp.ledger.exceptions import LedgerError, LedgerConflict
from substrapp.views.computeplan import create_compute_plan
from substrapp.views.filters_utils import filter_list
from substrapp.views.utils import (validate_key, get_success_create_code, LedgerException, get_channel_name)


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
            data = serializer.validated_data
            if data['rank'] == 0 and not data['compute_plan_id']:
                # Auto-create compute plan
                res = create_compute_plan(channel_name, data={})
                data['compute_plan_id'] = res['compute_plan_id']
            data = serializer.create(channel_name, data)
        except LedgerConflict as e:
            raise LedgerException({'message': str(e.msg), 'key': e.key}, e.status)
        except LedgerError as e:
            raise LedgerException({'message': str(e.msg)}, e.status)
        else:
            return data

    def _create(self, request):
        key = uuid.uuid4()
        data = {
            'key': key,
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

        return self.commit(serializer, get_channel_name(request))

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
            data = query_ledger(get_channel_name(request), fcn='queryTraintuples', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        query_params = request.query_params.get('search')
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
        validate_key(pk)
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
