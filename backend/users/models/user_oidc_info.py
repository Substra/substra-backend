from django.conf import settings
from django.db import models


class UserOidcInfo(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="oidc_info")
    openid_issuer = models.TextField()
    openid_subject = models.TextField()
    valid_until = models.DateTimeField()
    refresh_token = models.TextField(blank=True)
