import datetime
import logging
import threading

from django.conf import settings

LEDGER = getattr(settings, 'LEDGER', None)
logger = logging.getLogger(__name__)

LEDGER_CLIENT_TTL_SECONDS = 30

_client_ttl_delta = datetime.timedelta(0, LEDGER_CLIENT_TTL_SECONDS)
_threadLocal = threading.local()


class ClientWrapper:
    """
    Validate whether the password is of a maximum length.
    """
    _loop = None
    _client = None
    _expires_on = None
    _destroyed = False

    def __init__(self, now):
        (loop, client) = LEDGER['hfc']()
        self._loop = loop
        self._client = client
        self._expires_on = now + _client_ttl_delta
        logger.info("XXXXX Initializing")

    def has_expired(self, now):
        if self._destroyed:
            return True
        return self._expires_on < now

    async def close_grpc_channels(self):
        for name in self._client.peers:
            await self._client.peers[name]._channel.close()
        for name in self._client.orderers:
            await self._client.orderers[name]._channel.close()
        logger.info("XXXXX Destructing!")

    def destroy(self):
        if self._destroyed:
            return
        self._loop.run_until_complete(self.close_grpc_channels())
        del self._client
        self._loop.close()
        self._destroyed = True

    def __del__(self):
        self.destroy()


def get_hfc(force=False):
    logger.info("XXXXX Request")
    renew = force
    now = datetime.datetime.now()
    hfc_client = getattr(_threadLocal, 'hfc_client', None)
    if hfc_client is not None and hfc_client.has_expired(now):
        logger.info("XXXXX Too old!")
        renew = True
    if renew and hfc_client is not None:
        # sychronously destroy: we don't want to wait until the GC to close the connections.
        hfc_client.destroy()
        hfc_client = None
    if hfc_client is None:
        hfc_client = ClientWrapper(now)
        _threadLocal.hfc_client = hfc_client
    return (hfc_client._loop, hfc_client._client)


def invalidate_hfc_client():
    hfc_client = getattr(_threadLocal, 'hfc_client', None)
    if hfc_client is not None:
        # sychronously destroy: we don't want to wait until the GC to close the connections.
        hfc_client.destroy()
        _threadLocal.hfc_client = None
