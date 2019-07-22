from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.serializers import LedgerComputePlanSerializer
from substrapp.ledger_utils import query_ledger, LedgerError
from substrapp.views.utils import get_success_create_code, LedgerException


class ComputePlanViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        GenericViewSet):

    serializer_class = LedgerComputePlanSerializer

    def get_queryset(self):
        return []

    def perform_create(self, serializer):
        return serializer.save()

    def commit(self, serializer, fltask):
        # create on ledger
        try:
            data = serializer.create(serializer.validated_data)
        except LedgerError as e:
            raise LedgerException({'message': str(e.msg), 'fltask': fltask}, e.status)
        else:
            return data

    def _create(self, request):
        traintuples = []
        input_data = dict(request.data)
        for traintuple in input_data.get('traintuples', []):
            traintuples.append({
                'data_manager_key': traintuple.get('data_manager_key'),
                'train_data_sample_keys': traintuple.get('train_data_sample_keys', []),
                'traintuple_id': traintuple.get('traintuple_id'),
                'in_models_ids': traintuple.get('in_model_ids', []),
                'tag': traintuple.get('tag', ''),
            })
        data = {
            'algo_key': input_data.get('algo_key'),
            'objective_key': input_data.get('objective_key'),
            'traintuples': traintuples,
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Get traintuple fltask to handle 408 timeout in invoke_ledger
        args = serializer.get_args(serializer.validated_data)

        try:
            data = query_ledger(fcn='createComputePlan', args=args)
        except LedgerError as e:
            raise LedgerException({'message': str(e.msg)}, e.status)
        else:
            fltask = data.get('fltask')
            output_data = self.commit(serializer, fltask)
            return output_data

    def create(self, request, *args, **kwargs):
        try:
            data = self._create(request)
        except LedgerException as e:
            return Response(e.data, status=e.st)
        else:
            headers = self.get_success_headers(data)
            st = get_success_create_code()
            return Response(data, status=st, headers=headers)
