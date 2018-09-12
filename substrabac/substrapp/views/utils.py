import hashlib
import os
from urllib.parse import unquote

from django.http import FileResponse
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

from substrapp.utils import queryLedger


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


def getObjectFromLedger(pk):
    # get instance from remote node
    data, st = queryLedger({
        'org': settings.LEDGER['org'],
        'peer': settings.LEDGER['peer'],
        'args': '{"Args":["query","%s"]}' % pk
    })

    if st != 200:
        raise Exception(data)

    if data['permissions'] == 'all':
        return data
    else:
        raise Exception('Not Allowed')


class ComputeHashMixin(object):
    def compute_hash(self, file):

        sha256_hash = hashlib.sha256()
        if isinstance(file, str):
            file = file.encode()
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
            getObjectFromLedger(pk)
        except Exception as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            object = self.get_object()

            data = getattr(object, field)
            return CustomFileResponse(open(data.path, 'rb'), as_attachment=True, filename=os.path.basename(data.path))
