from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken as DRFObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from api.views.utils import ApiResponse
from api.views.utils import get_channel_name
from libs.permissions import IsAuthorized
from libs.user_login_throttle import UserLoginThrottle
from orchestrator import get_orchestrator_client
from substrapp.utils import get_owner
from users.models.token import BearerToken
from users.models.token import ImplicitBearerToken
from users.models.token import get_implicit_bearer_token
from users.serializers.token import BearerTokenSerializer
from users.serializers.token import ImplicitBearerTokenSerializer

from .exceptions import ImplicitLoginDisabled


class ObtainBearerToken(DRFObtainAuthToken):
    """
    get a Bearer token from {username, password}
    """

    # use legacy token
    authentication_classes = []
    throttle_classes = [AnonRateThrottle, UserLoginThrottle]

    def post(self, request, *args, **kwargs):
        if not settings.EXPIRY_TOKEN_ENABLED:
            raise ImplicitLoginDisabled()

        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        token = get_implicit_bearer_token(user)
        return ApiResponse(ImplicitBearerTokenSerializer(token, include_payload=True).data)


class AuthenticatedBearerToken(DRFObtainAuthToken):
    """
    get a Bearer token if you're already authenticated somehow
    """

    permission_classes = [IsAuthorized]

    def post(self, request, *args, **kwargs):
        s = BearerTokenSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        token = BearerToken.objects.create(user=request.user, **s.validated_data)
        return ApiResponse(BearerTokenSerializer(token, include_payload=True).data)


class ActiveBearerTokens(APIView):
    """
    list Bearer tokens for a user
    """

    permission_classes = [IsAuthorized]

    def get(self, request, *args, **kwargs):
        tokens = [
            BearerTokenSerializer(token).data
            for token in BearerToken.objects.filter(user=request.user).order_by("-created")
        ]
        implicit_tokens = [
            ImplicitBearerTokenSerializer(token).data
            for token in ImplicitBearerToken.objects.filter(user=request.user).order_by("-created")
        ]
        return ApiResponse(
            {
                "tokens": tokens,
                "implicit_tokens": implicit_tokens,
            }
        )

    def delete(self, request, *args, **kwargs):
        for model in [BearerToken, ImplicitBearerToken]:
            tokens = model.objects.filter(id=request.GET.get("id"))
            if len(tokens) == 1 and request.user == tokens[0].user:
                tokens[0].delete()
                return ApiResponse(data={"detail": "Token removed"}, status=status.HTTP_200_OK)
        return ApiResponse(data={"detail": "Token not found"}, status=status.HTTP_404_NOT_FOUND)


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
            channel = settings.CHANNELS[channel_name]

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
