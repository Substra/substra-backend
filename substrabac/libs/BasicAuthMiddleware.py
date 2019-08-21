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

    def __init__(self, get_response):
        self.get_response = get_response

    def not_authenticated(self):
        response = HttpResponse(html_template, content_type="text/html")
        response['WWW-Authenticate'] = 'Basic realm="Administrator area"'
        response.status_code = 401
        return response

    def __call__(self, request):
        server_username = settings.BASICAUTH_USERNAME
        server_password = settings.BASICAUTH_PASSWORD

        if not server_username or not server_password:
            return self.not_authenticated()

        if request.method != 'OPTIONS':
            return self.not_authenticated()

        if 'HTTP_AUTHORIZATION' not in request.META:
            return self.not_authenticated()

        header = request.META['HTTP_AUTHORIZATION']
        (method, auth) = header.split(' ', 1)
        if 'basic' != method.lower():
            return self.not_authenticated()

        auth = base64.b64decode(auth.strip()).decode('utf-8')
        username, password = auth.split(':', 1)
        if username != server_username or password != server_password:
            return self.not_authenticated()

        return self.get_response(request)
