from django.conf import settings
from django.urls import reverse
from rest_framework.authtoken.models import Token as BearerToken
from rest_framework.authtoken.views import ObtainAuthToken as DRFObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from libs.user_login_throttle import UserLoginThrottle
from substrapp.orchestrator import get_orchestrator_client
from substrapp.utils import get_owner
from users.utils import bearer_token as bearer_token_utils


def _bearer_token_dict(token: BearerToken, include_payload: bool = True) -> dict:
    d = {"created": token.created, "expires_at": bearer_token_utils.expires_at(token)}
    if include_payload:
        d["token"] = token.key
    return d


class ObtainBearerToken(DRFObtainAuthToken):
    """
    get a Bearer token from {username, password}
    """

    authentication_classes = []
    throttle_classes = [AnonRateThrottle, UserLoginThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if settings.TOKEN_STRATEGY == "reuse":  # nosec
            token, created = BearerToken.objects.get_or_create(user=user)
            # handle_token_expiration will check whether the token is expired
            # and will generate a new one if necessary
            is_expired, token = bearer_token_utils.handle_token_expiration(token)
        else:
            # token should be new each time, remove the old one
            BearerToken.objects.filter(user=user).delete()
            token = BearerToken.objects.create(user=user)
        return ApiResponse(_bearer_token_dict(token))


class AuthenticatedBearerToken(DRFObtainAuthToken):
    """
    get a Bearer token if you're already authenticated somehow
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # create a new token each time (you don't want a token that is about to expire)
        BearerToken.objects.filter(user=request.user).delete()
        token = BearerToken.objects.create(user=request.user)
        return ApiResponse(_bearer_token_dict(token))


class ActiveBearerTokens(APIView):
    """
    list Bearer tokens for a user
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        tokens = BearerToken.objects.filter(user=request.user)

        return ApiResponse({"tokens": [_bearer_token_dict(token, include_payload=False) for token in tokens]})


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
                "name": settings.OIDC["OP"]["DISPLAY_NAME"],
                "login_url": reverse("oidc_authentication_init"),
            }

        return ApiResponse(res)


obtain_auth_token = ObtainBearerToken.as_view()
obtain_auth_token_already_authenticated = AuthenticatedBearerToken.as_view()
active_bearer_tokens = ActiveBearerTokens.as_view()
info_view = Info.as_view()
