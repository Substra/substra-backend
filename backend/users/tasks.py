import logging
from rest_framework_simplejwt.utils import aware_utcnow

from backend.celery import app


logger = logging.getLogger(__name__)


@app.task(ignore_result=True)
def flush_expired_tokens():
    """Flush expired tokens

    Adapted from DRF simplejwt flushexpiredtokens command
    """
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
    tokens = OutstandingToken.objects.filter(expires_at__lte=aware_utcnow())
    logger.info(f'Flushing {len(tokens)} expired tokens')
    tokens.delete()
