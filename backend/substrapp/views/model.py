import tempfile
import logging
from functools import wraps
from django.conf import settings
from django.middleware.gzip import GZipMiddleware
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from node.authentication import NodeUser
from substrapp.models import Model
from substrapp.ledger_utils import query_ledger, get_object_from_ledger, LedgerError
from substrapp.views.utils import validate_pk, get_remote_asset, PermissionMixin
from substrapp.views.filters_utils import filter_list

logger = logging.getLogger(__name__)


class ModelViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    queryset = Model.objects.all()
    ledger_query_call = 'queryModelDetails'
    # permission_classes = (permissions.IsAuthenticated,)

    def create_or_update_model(self, traintuple, pk):
        if traintuple['outModel'] is None:
            raise Exception(f'This traintuple related to this model key {pk} does not have a outModel')

        # get model from remote node
        url = traintuple['outModel']['storageAddress']

        content = get_remote_asset(url, traintuple['creator'], traintuple['key'])

        # write model in local db for later use
        tmp_model = tempfile.TemporaryFile()
        tmp_model.write(content)
        instance, created = Model.objects.update_or_create(pkhash=pk, validated=True)
        instance.file.save('model', tmp_model)

        return instance

    def _retrieve(self, pk):
        validate_pk(pk)

        data = get_object_from_ledger('mychannel', pk, self.ledger_query_call)

        compatible_tuple_types = ['traintuple', 'compositeTraintuple', 'aggregatetuple']
        any_data = any(list(map(lambda x: x in data, compatible_tuple_types)))

        if not any_data:
            raise Exception(
                'Invalid model: missing traintuple, compositeTraintuple or aggregatetuple field'
            )

        return data

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            data = self._retrieve(pk)
        except LedgerError as e:
            logger.exception(e)
            return Response({'message': str(e.msg)}, status=e.status)
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)}, status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        try:
            data = query_ledger('mychannel', fcn='queryModels', args=[])
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)

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

        return Response(models_list, status=status.HTTP_200_OK)


def gzip_action(func):
    gz = GZipMiddleware()

    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        resp = func(self, request, *args, **kwargs)
        return gz.process_response(request, resp)

    if getattr(settings, 'GZIP_MODELS'):
        return wrapper
    return func


class ModelPermissionViewSet(PermissionMixin,
                             GenericViewSet):

    queryset = Model.objects.all()
    ledger_query_call = 'queryModelPermissions'

    def has_access(self, user, asset):
        """Returns true if API consumer can access asset data."""
        if user.is_anonymous:  # safeguard, should never happened
            return False

        # user cannot download model, only node can
        if not (type(user) is NodeUser):
            return False

        permissions = asset['process']
        node_id = user.username

        return permissions['public'] or node_id in permissions['authorizedIDs']

    @gzip_action
    @action(detail=True)
    def file(self, request, *args, **kwargs):
        return self.download_local_file(request, django_field='file')
