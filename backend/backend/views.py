import yaml

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, renderer_classes
from rest_framework import response, schemas
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
from rest_framework.compat import coreapi

from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from django.conf.urls import url, include

from libs.expiry_token_authentication import token_expire_handler, expires_at
from substrapp.urls import router

from requests.compat import urlparse


class SchemaGenerator(schemas.SchemaGenerator):
    def get_link(self, path, method, view):
        """Custom the coreapi using the func.__doc__ .

        if __doc__ of the function exist, use the __doc__ building the coreapi. else use the default serializer.

        __doc__ in yaml format, eg:
        nota for type: Required.
        The type of the parameter. Since the parameter is not located at the request body,
        it is limited to simple types (that is, not an object).
        The value MUST be one of "string", "number", "integer", "boolean", "array" or "file".
        If type is "file", the consumes MUST be either "multipart/form-data", " application/x-www-form-urlencoded"
        or both and the parameter MUST be in "formData".

        ---

        desc: the desc of this api.
        ret: when success invoked, return xxxx
        err: when error occured, return xxxx
        input:
        - name: mobile
          desc: the mobile number
          type: string
          required: true
          location: form
        - name: promotion
          desc: the activity id
          type: integer
          required: true
          location: form
        """
        fields = self.get_path_fields(path, method, view)
        func = getattr(view, view.action) if getattr(view, 'action', None) else None
        _method_desc = ''
        if func and func.__doc__:
            a = func.__doc__.split('---')
            if len(a) == 2:
                try:
                    yaml_doc = yaml.load(a[1])
                except BaseException:
                    pass
                else:
                    if 'desc' in yaml_doc:
                        desc = yaml_doc.get('desc', '')
                        ret = yaml_doc.get('ret', '')
                        err = yaml_doc.get('err', '')
                        _method_desc = desc + '\n<br/>' + 'return: ' + ret + '<br/>' + 'error: ' + err
                        params = yaml_doc.get('input', [])
                        for i in params:
                            _name = i.get('name')
                            _desc = i.get('desc')
                            _required = i.get('required', True)
                            _type = i.get('type', 'string')
                            _location = i.get('location', 'form')
                            field = coreapi.Field(
                                name=_name,
                                location=_location,
                                required=_required,
                                description=_desc,
                                type=_type
                            )
                            fields.append(field)
            else:
                _method_desc = a[0]
                fields += self.get_serializer_fields(path, method, view)
        else:
            fields += self.get_serializer_fields(path, method, view)

        fields += self.get_pagination_fields(path, method, view)
        fields += self.get_filter_fields(path, method, view)

        if fields and any([f.location in ('form', 'body') for f in fields]):
            encoding = self.get_encoding(path, method, view)
        else:
            encoding = None

        if self.url and path.startswith('/'):
            path = path[1:]

        return coreapi.Link(
            url=urlparse.urljoin(self.url, path),
            action=method.lower(),
            encoding=encoding,
            fields=fields,
            description=_method_desc
        )


@api_view()
@renderer_classes([OpenAPIRenderer, SwaggerUIRenderer])
def schema_view(request):
    generator = SchemaGenerator(
        title='Substra Backend API',
        patterns=[url(r'^/', include([url(r'^', include(router.urls))]))])
    return response.Response(generator.get_schema(request=request))


class ExpiryObtainAuthToken(ObtainAuthToken):
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # token_expire_handler will check, if the token is expired it will generate new one
        is_expired, token = token_expire_handler(token)

        return Response({
            'token': token.key,
            'expires_at': expires_at(token)
        })


obtain_auth_token = ExpiryObtainAuthToken.as_view()
