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
        if not settings.DEBUG:
            raise MiddlewareNotUsed

        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
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
                if username == settings.BASICAUTH_USERNAME and password == settings.BASICAUTH_PASSWORD:
                    del request.META['HTTP_AUTHORIZATION']
                    return None

            return self.get_response(request)
