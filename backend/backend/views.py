from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
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
from users.models.token import BearerToken


def _bearer_token_dict(token: BearerToken, include_payload: bool = True) -> dict:
    d = {"created_at": token.created, "expires_at": token.expires_at(), "note": token.note, "token_id": token.token_id}
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
        token = BearerToken.objects.create(user=user, expiry=request.GET.get("expiry"), note=request.GET.get("note"))
        return ApiResponse(_bearer_token_dict(token))


class AuthenticatedBearerToken(DRFObtainAuthToken):
    """
    get a Bearer token if you're already authenticated somehow
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        token = BearerToken.objects.create(
            user=request.user, expiry=request.GET.get("expiry"), note=request.GET.get("note")
        )
        return ApiResponse(_bearer_token_dict(token))


class ActiveBearerTokens(APIView):
    """
    list Bearer tokens for a user
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        tokens = BearerToken.objects.filter(user=request.user)

        return ApiResponse({"tokens": [_bearer_token_dict(token, include_payload=False) for token in tokens]})

    def delete(self, request, *args, **kwargs):
        if BearerToken.objects.filter(token_id=request.GET.get("id")):
            token = BearerToken.objects.get(token_id=request.GET.get("id"))
            if request.user == token.user:
                token.delete()
                return HttpResponse("Authorized, token removed", status=200)
            else:
                return HttpResponse("Unauthorized, token was NOT removed", status=401)
        else:
            return HttpResponse("Token not found", status=404)


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
