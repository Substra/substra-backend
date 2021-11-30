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
from django.conf.urls import url
from django.conf.urls.static import static
from django.urls import include
from django.urls import path
from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.views import SpectacularRedocView
from drf_spectacular.views import SpectacularSwaggerView
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.settings import api_settings

from backend.views import info_view
from backend.views import obtain_auth_token
from node.urls import router as node_router
from substrapp.urls import compute_plan_router
from substrapp.urls import router
from users.urls import router as user_router

urlpatterns = (
    [
        url(
            r"^",
            include(
                [
                    url(r"^", include((router.urls + compute_plan_router.urls, "substrapp"))),
                    url(r"^", include((node_router.urls, "node"))),
                    url(r"^", include((user_router.urls, "user"))),  # for secure jwt authent
                    url(r"^api-token-auth/", obtain_auth_token),  # for expiry token authent
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
    urlpatterns += [url(r"^api-auth/", include("rest_framework.urls"))]

urlpatterns += [url(r"^info/", info_view)]

if settings.SUBPATH:
    urlpatterns = [url(fr"^{settings.SUBPATH}", include(urlpatterns))]
