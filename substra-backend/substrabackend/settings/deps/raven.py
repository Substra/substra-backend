import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get("RAVEN_URL"),
    integrations=[DjangoIntegration()]
)
