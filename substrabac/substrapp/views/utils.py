import hashlib
import json
import os

from django.http import FileResponse
from rest_framework.response import Response

from authent.models import InternalAuthent
from substrabac.settings.deps.ledger import get_csr, get_hashed_modulus
from substrapp.ledger_utils import get_object_from_ledger, LedgerError, LedgerForbidden, LedgerUnauthorized

from django.conf import settings
from rest_framework import status

from substrapp.utils import get_hash

LEDGER = getattr(settings, 'LEDGER', None)


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

        # test with
        # curl --cookie "username=chu-nantes;password=chu-nantespw" --header "Accept:text/html;version=0.0, */*;version=0.0"  -XGET http://owkin.substrabac:8000/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/file/ # noqa

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        try:
            x = get_object_from_ledger(pk, self.ledger_query_call)
        except LedgerError as e:
            return Response({'message': str(e.msg)}, status=e.status)
        else:
            if x['permissions'] != 'all':
                username = self.request.COOKIES.get('username', None)
                pwd = self.request.COOKIES.get('password', None)

                # owner permissions
                # TODO check referrer, if not self, raise Permission Denied
                # TODO should be avoided
                # signcert can expire, asset owner should be done on modulus
                if x['permissions'] == '[]':
                    # get owner of asset
                    asset_owner = x['owner']
                    # get node owner
                    self_owner = get_hash(settings.LEDGER['signcert'])

                    # check if Node user is owner
                    if asset_owner != self_owner:
                        raise LedgerUnauthorized('Permission denied')
                else:
                    if username is None or pwd is None:
                        raise Exception('Missing cookies username/password')
                    try:
                        permissions = json.loads(x['permissions'])
                    except Exception as e:
                        raise Exception(f'cannot load asset permissions, error: {str(e)}')
                    else:
                        csr = get_csr(LEDGER['hfc_ca']['pkey'], username)
                        try:
                            enrollment = LEDGER['hfc_ca']['client'].enroll(username, pwd, csr=csr)
                        except Exception as e:
                            raise LedgerForbidden(f'Not allowed, error: {str(e)}')
                        else:
                            hashed_modulus = get_hashed_modulus(enrollment.cert)
                            if not InternalAuthent.objects.filter(permission__name__in=permissions, modulus=hashed_modulus):
                                raise LedgerUnauthorized('Permission denied')

            obj = self.get_object()
            data = getattr(obj, field)
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


class LedgerException(Exception):
    def __init__(self, data, st):
        self.data = data
        self.st = st
        super(LedgerException).__init__()


class ValidationException(Exception):
    def __init__(self, data, pkhash, st):
        self.data = data
        self.pkhash = pkhash
        self.st = st
        super(ValidationException).__init__()


def get_success_create_code():
    if getattr(settings, 'LEDGER_SYNC_ENABLED'):
        return status.HTTP_201_CREATED
    else:
        return status.HTTP_202_ACCEPTED
