import structlog
from rest_framework_simplejwt.utils import aware_utcnow

from backend.celery import app

logger = structlog.get_logger(__name__)


@app.task(ignore_result=True)
def flush_expired_tokens():
    """Flush expired tokens

    Adapted from DRF simplejwt flushexpiredtokens command
    """
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

    tokens = OutstandingToken.objects.filter(expires_at__lte=aware_utcnow())
    logger.info("Flushing expired tokens", num_tokens=len(tokens))
    tokens.delete()
