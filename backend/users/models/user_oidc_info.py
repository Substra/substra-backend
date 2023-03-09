from django.conf import settings
from django.db import models


class UserOidcInfo(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="oidc_info")
    openid_subject = models.CharField(max_length=255)
