import hashlib
from urllib.parse import unquote

import requests
from rest_framework import status
from rest_framework.response import Response


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


class computeHashMixin(object):
    def compute_hash(self, file):

        sha256_hash = hashlib.sha256()
        if isinstance(file, str):
            file = file.encode()
        sha256_hash.update(file)
        computedHash = sha256_hash.hexdigest()

        return computedHash

    def get_computed_hash(self, url):
        try:
            r = requests.get(url)
        except:
            raise Response({'message': 'Failed to check hash due to failed file fetching %s' % url}, status.HTTP_400_BAD_REQUEST)
        else:
            if r.status_code == 200:
                return self.compute_hash(r.content)

            raise Response({'message': 'Failed to check hash due to wrong returned status code %s' % r.status_code}, status.HTTP_400_BAD_REQUEST)
