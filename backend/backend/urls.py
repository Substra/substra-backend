"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include
from django.urls import path
from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.views import SpectacularRedocView
from drf_spectacular.views import SpectacularSwaggerView
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.settings import api_settings

from api.urls import urlpatterns
from backend.views import active_bearer_tokens
from backend.views import info_view
from backend.views import obtain_auth_token
from backend.views import obtain_auth_token_already_authenticated
from organization.urls import router as organization_router
from users.urls import router as user_router

urlpatterns = (
    [
        path(
            r"",
            include(
                [
                    path("", include((urlpatterns, "api"))),
                    path("", include((organization_router.urls, "organization"))),
                    path("", include((user_router.urls, "user"))),  # for secure jwt authent
                    path("api-token-auth/", obtain_auth_token),  # for expiry token authent
                    path("api-token/", obtain_auth_token_already_authenticated),
                    path("active-api-tokens/", active_bearer_tokens),
                ]
            ),
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + [  # OpenAPI spec and UI
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "schema/swagger-ui/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "schema/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]
)

# only allow session authentication is the browsable API is enabled
if BrowsableAPIRenderer in api_settings.DEFAULT_RENDERER_CLASSES:
    urlpatterns += [path("api-auth/", include("rest_framework.urls"))]

urlpatterns += [path("info/", info_view)]

if hasattr(settings, "OIDC") and settings.OIDC.get("ENABLED", False):
    urlpatterns += [path("oidc/", include("mozilla_django_oidc.urls"))]

if settings.SUBPATH:
    urlpatterns = [path(f"{settings.SUBPATH}", include(urlpatterns))]
