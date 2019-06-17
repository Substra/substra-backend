import os
import tempfile
import logging
from django.http import Http404
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.models import Model
from substrapp.serializers import ModelSerializer

from substrapp.utils import get_from_node
from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError
from substrapp.views.utils import ComputeHashMixin, CustomFileResponse, validate_pk
from substrapp.views.filters_utils import filter_list


class ModelViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   ComputeHashMixin,
                   GenericViewSet):
    queryset = Model.objects.all()
    serializer_class = ModelSerializer
    ledger_query_call = 'queryModelDetails'
    # permission_classes = (permissions.IsAuthenticated,)

    def create_or_update_model(self, traintuple, pk):
        if traintuple['outModel'] is None:
            raise Exception(f'This traintuple related to this model key {pk} does not have a outModel')

        # get model from remote node
        url = traintuple['outModel']['storageAddress']

        response = get_from_node(url)

        # verify model received has a good pkhash
        try:
            computed_hash = self.compute_hash(response.content, traintuple['key'])
        except Exception:
            raise Exception('Failed to fetch outModel file')
        else:
            if computed_hash != pk:
                msg = 'computed hash is not the same as the hosted file. ' \
                      'Please investigate for default of synchronization, corruption, or hacked'
                raise Exception(msg)

        # write model in local db for later use
        tmp_model = tempfile.TemporaryFile()
        tmp_model.write(response.content)
        instance, created = Model.objects.update_or_create(pkhash=pk, validated=True)
        instance.file.save('model', tmp_model)

        return instance

    def _retrieve(self, pk):
        validate_pk(pk)
        # get instance from remote node
        data = get_object_from_ledger(pk, self.ledger_query_call)

        # Try to get it from local db, else create it in local db
        try:
            instance = self.get_object()
        except Http404:
            instance = None
        finally:
            if not instance or not instance.file:
                instance = self.create_or_update_model(data['traintuple'],
                                                       data['traintuple']['outModel']['hash'])

                # For security reason, do not give access to local file address
                # Restrain data to some fields
                # TODO: do we need to send creation date and/or last modified date ?
                serializer = self.get_serializer(instance, fields=('owner', 'pkhash'))
                data.update(serializer.data)

                return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(pk)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        except Exception as e:
            return Response({'message': str(e)}, status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger(fcn='queryModels', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        data = data if data else []

        models_list = [data]

        query_params = request.query_params.get('search', None)
        if query_params is not None:
            try:
                models_list = filter_list(
                    object_type='model',
                    data=data,
                    query_params=query_params)
            except LedgerError as e:
                return Response({'message': str(e.msg)}, status=e.status)
            except Exception as e:
                logging.exception(e)
                return Response(
                    {'message': f'Malformed search filters {query_params}'},
                    status=status.HTTP_400_BAD_REQUEST)

        return Response(models_list, status=status.HTTP_200_OK)

    @action(detail=True)
    def file(self, request, *args, **kwargs):
        model_object = self.get_object()
        data = getattr(model_object, 'file')
        return CustomFileResponse(open(data.path, 'rb'), as_attachment=True, filename=os.path.basename(data.path))

    @action(detail=True)
    def details(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            data = get_object_from_ledger(pk, self.ledger_query_call)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

        return Response(data, status=status.HTTP_200_OK)
