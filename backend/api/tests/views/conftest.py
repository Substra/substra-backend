import functools
import pathlib
from typing import Final

import pytest
from django import conf
from rest_framework import test

from substrapp.tests import common

_CHANNEL_NAME: Final[str] = "mychannel"
_EXTRA_HTTP_HEADERS: Final[dict[str, str]] = {"HTTP_SUBSTRA_CHANNEL_NAME": _CHANNEL_NAME}


@pytest.fixture(autouse=True)
def _set_settings(settings: conf.Settings, tmp_path: pathlib.Path):
    settings.MEDIA_ROOT = tmp_path.resolve()
    settings.LEDGER_CHANNELS = {_CHANNEL_NAME: {"chaincode": {"name": "mycc"}, "model_export_enabled": True}}


@pytest.fixture
def authenticated_client() -> test.APIClient:
    client = common.AuthenticatedClient()

    client.get = functools.partial(client.get, **_EXTRA_HTTP_HEADERS)
    client.post = functools.partial(client.post, **_EXTRA_HTTP_HEADERS)

    return client


@pytest.fixture
def api_client() -> test.APIClient:
    return test.APIClient()
