import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://0521084433564ed8983a0116500ac51f@sentry.io/1312809",
    integrations=[DjangoIntegration()]
)
