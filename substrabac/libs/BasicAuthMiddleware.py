from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponse
from django.conf import settings

import base64


html_template = """
<html>
    <title>Auth required</title>
    <body>
        <h1>Authorization Required</h1>
    </body>
</html>
"""


class BasicAuthMiddleware:
    def unauthed(self):
        response = HttpResponse(html_template, content_type="text/html")
        response['WWW-Authenticate'] = 'Basic realm="Administrator area"'
        response.status_code = 401
        return response

    def __init__(self, get_response):
        if settings.DEBUG:
            raise MiddlewareNotUsed

        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        username = getattr(settings, 'BASICAUTH_USERNAME', None)
        password = getattr(settings, 'BASICAUTH_PASSWORD', None)

        if username not in (None, '') and password not in (None, ''):
            if request.method != 'OPTIONS':
                if 'HTTP_AUTHORIZATION' not in request.META:
                    return self.unauthed()
                else:
                    authentication = request.META['HTTP_AUTHORIZATION']
                    (authmeth, auth) = authentication.split(' ', 1)
                    if 'basic' != authmeth.lower():
                        return self.unauthed()
                    auth = base64.b64decode(auth.strip()).decode('utf-8')
                    username, password = auth.split(':', 1)
                    if username != settings.BASICAUTH_USERNAME or password != settings.BASICAUTH_PASSWORD:
                        return self.unauthed()

        return self.get_response(request)
