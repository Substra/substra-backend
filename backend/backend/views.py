from django.conf import settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from libs.expiry_token_authentication import expires_at
from libs.expiry_token_authentication import token_expire_handler
from libs.user_login_throttle import UserLoginThrottle
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import get_owner


def _get_bearer_token(user):
    if settings.TOKEN_STRATEGY == "reuse":  # nosec
        token, created = Token.objects.get_or_create(user=user)
        # token_expire_handler will check whether the token is expired
        # and will generate a new one if necessary
        is_expired, token = token_expire_handler(token)
    else:
        # token should be new each time, remove the old one
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
    return token


class ExpiryObtainAuthToken(ObtainAuthToken):
    """
    get a Bearer token from {username, password}
    """

    authentication_classes = []
    throttle_classes = [AnonRateThrottle, UserLoginThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token = _get_bearer_token(user)
        return ApiResponse({"token": token.key, "expires_at": expires_at(token)})


class AuthenticatedAuthToken(ObtainAuthToken):
    """
    get a Bearer token if you're already authenticated somehow
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        token = _get_bearer_token(request.user)
        return ApiResponse({"token": token.key, "expires_at": expires_at(token)})


class Info(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        res = {
            "host": settings.DEFAULT_DOMAIN,
            "organization_id": get_owner(),
            "organization_name": settings.ORG_NAME,
            "config": {},
            "auth": {},
        }

        if request.user.is_authenticated:
            channel_name = get_channel_name(request)
            channel = settings.LEDGER_CHANNELS[channel_name]

            orchestrator_versions = None

            if not settings.ISOLATED:
                with get_orchestrator_client(channel_name) as client:
                    orchestrator_versions = client.query_version()

            res["channel"] = channel_name
            res["version"] = settings.BACKEND_VERSION
            res["orchestrator_version"] = orchestrator_versions.server if orchestrator_versions is not None else None
            res["config"]["model_export_enabled"] = channel["model_export_enabled"]

            res["user"] = request.user.get_username()
            if hasattr(request.user, "channel"):
                res["user_role"] = request.user.channel.role

            if orchestrator_versions and orchestrator_versions.chaincode:
                res["chaincode_version"] = orchestrator_versions.chaincode

        if settings.OIDC["ENABLED"]:
            res["auth"]["oidc"] = {
                "name": settings.OIDC["OP_DISPLAY_NAME"],
                "login_url": reverse("oidc_authentication_init"),
            }

        return ApiResponse(res)


obtain_auth_token = ExpiryObtainAuthToken.as_view()
obtain_auth_token_already_authenticated = AuthenticatedAuthToken.as_view()
info_view = Info.as_view()
