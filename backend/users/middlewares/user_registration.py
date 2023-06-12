from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import PermissionDenied


class UserRegistration:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        if not isinstance(request.user, AnonymousUser):
            print(request.user)
            if not hasattr(request.user, "channel"):
                raise PermissionDenied(
                    detail={"error_code": "registration_error", "description": "User is not registered"}
                )

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
