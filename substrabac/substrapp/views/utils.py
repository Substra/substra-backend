import hashlib
import os

from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.response import Response

from substrapp.ledger_utils import getObjectFromLedger


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
        except Http404:
            return Response(f'No element with key {pk}', status=status.HTTP_404_NOT_FOUND)
        else:
            object = self.get_object()

            data = getattr(object, field)
            return CustomFileResponse(open(data.path, 'rb'), as_attachment=True, filename=os.path.basename(data.path))


def find_primary_key_error(validation_error, key_name='pkhash'):
    detail = validation_error.detail

    def find_unique_error(detail_dict):
        for key, errors in detail_dict.items():
            if key != key_name:
                continue
            for error in errors:
                if error.code == 'unique':
                    return error

        return None

    # according to the rest_framework documentation,
    # validation_error.detail could be either a dict, a list or a nested
    # data structure

    if isinstance(detail, dict):
        return find_unique_error(detail)
    elif isinstance(detail, list):
        for sub_detail in detail:
            if isinstance(sub_detail, dict):
                unique_error = find_unique_error(sub_detail)
                if unique_error is not None:
                    return unique_error

    return None


def validate_pk(pk):
    if len(pk) != 64:
        raise Exception(f'Wrong pk {pk}')

    try:
        int(pk, 16)  # test if pk is correct (hexadecimal)
    except ValueError:
        raise Exception(f'Wrong pk {pk}')
