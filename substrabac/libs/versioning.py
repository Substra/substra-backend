from rest_framework import exceptions
from rest_framework.utils.mediatypes import _MediaType
from rest_framework.versioning import AcceptHeaderVersioning


class AcceptHeaderVersioningRequired(AcceptHeaderVersioning):

    def determine_version(self, request, *args, **kwargs):
        media_type = _MediaType(request.accepted_media_type)

        version = media_type.params.get(self.version_param, None)
        if version is None:
            raise exceptions.NotAcceptable('A version is required.')

        return super(AcceptHeaderVersioningRequired, self).determine_version(request, *args, **kwargs)
