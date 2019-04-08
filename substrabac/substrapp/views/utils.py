import hashlib
import os
from urllib.parse import unquote

from django.http import FileResponse
from rest_framework import status
from rest_framework.response import Response

from substrapp.utils import queryLedger


class JsonException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super(JsonException, self).__init__()


def get_filters(query_params):
    filters = []
    groups = query_params.split('-OR-')
    for idx, group in enumerate(groups):

        # init
        filters.append({})

        # get number of subfilters and decode them
        subfilters = [unquote(x) for x in group.split(',')]

        for subfilter in subfilters:
            el = subfilter.split(':')

            # get parent
            parent = el[0]
            subparent = el[1]
            value = el[2]

            filter = {
                subparent: [value]
            }

            if not len(filters[idx]):  # create and add it
                filters[idx] = {
                    parent: filter
                }
            else:  # add it
                if parent in filters[idx]:  # add
                    if el[1] in filters[idx][parent]:  # concat in subparent
                        filters[idx][parent][subparent].extend([value])
                    else:  # add new subparent
                        filters[idx][parent].update(filter)
                else:  # create
                    filters[idx].update({parent: filter})

    return filters


def getObjectFromLedger(pk, query):
    # get instance from remote node
    data, st = queryLedger({
        'args': f'{{"Args":["{query}","{pk}"]}}'
    })

    if st != status.HTTP_200_OK:
        raise JsonException(data)

    if 'permissions' not in data or data['permissions'] == 'all':
        return data
    else:
        raise Exception('Not Allowed')


class ComputeHashMixin(object):
    def compute_hash(self, file, key=None):

        sha256_hash = hashlib.sha256()
        if isinstance(file, str):
            file = file.encode()

        if key is not None and isinstance(key, str):
            file += key.encode()

        sha256_hash.update(file)
        computedHash = sha256_hash.hexdigest()

        return computedHash


class CustomFileResponse(FileResponse):
    def set_headers(self, filelike):
        super(CustomFileResponse, self).set_headers(filelike)

        self['Access-Control-Expose-Headers'] = 'Content-Disposition'


class ManageFileMixin(object):
    def manage_file(self, field):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        # TODO get cert for permissions check

        try:
            getObjectFromLedger(pk, self.ledger_query_call)
        except Exception as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            object = self.get_object()

            data = getattr(object, field)
            return CustomFileResponse(open(data.path, 'rb'), as_attachment=True, filename=os.path.basename(data.path))


def find_primary_key_error(validation_error, key_name='pkhash'):
    detail = validation_error.detail

    if not isinstance(detail, dict):
        # XXX according to the rest_framework documentation,
        #     validation_error.detail could be either a dict, a list or a
        #     nested data structure
        return None

    for key, errors in detail.items():
        if key != key_name:
            continue
        for error in errors:
            if error.code == 'unique':
                return error
    return None
