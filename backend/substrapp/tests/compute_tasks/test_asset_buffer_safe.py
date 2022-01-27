import os
from tempfile import TemporaryDirectory
from typing import Callable

import pytest

from substrapp.compute_tasks.asset_buffer import _add_datasample_to_buffer_internal
from substrapp.compute_tasks.asset_buffer import _add_model_to_buffer_internal
from substrapp.compute_tasks.asset_buffer import _add_opener_to_buffer_internal
from substrapp.compute_tasks.asset_buffer import add_to_buffer_safe

CHANNEL = "mychannel"
DUMMY_CONTENT_START = "some "
DUMMY_CONTENT_END = "content"
DUMMY_CONTENT = f"{DUMMY_CONTENT_START}{DUMMY_CONTENT_END}"


class DownloadAssetException(Exception):
    pass


@pytest.mark.parametrize(
    "func", [_add_model_to_buffer_internal, _add_opener_to_buffer_internal, _add_datasample_to_buffer_internal]
)
def test_add_methods_is_safe(func: Callable):
    """Ensure the method is decorated with @add_to_buffer_safe"""
    assert func.is_asset_buffer_safe


@pytest.mark.parametrize("raise_exception", [False, True])
def test_add_model_safe(raise_exception: bool):
    """Ensure a function protected with @add_to_buffer_safe is indeed safe"""

    with TemporaryDirectory() as tmpdir:
        asset_path = os.path.join(tmpdir, "asset")
        try:
            _add_asset_to_buffer(raise_exception, dst=asset_path)
        except DownloadAssetException:
            if raise_exception:
                pass

        # If _add_asset_to_buffer raised an exception, the asset should have been deleted.
        # Else the asset should be present.
        if raise_exception:
            with pytest.raises(FileNotFoundError):
                with open(asset_path, "r") as f:
                    contents = f.read()
        else:
            with open(asset_path, "r") as f:
                contents = f.read()
                assert contents == DUMMY_CONTENT


@add_to_buffer_safe
def _add_asset_to_buffer(raise_exception: bool, dst=str) -> None:
    """
    Write an asset to the asset buffer.

    If raise_exception is True, raise an exception in the middle of the writing process.
    """
    with open(dst, "w") as f:
        f.write(DUMMY_CONTENT_START)

    if raise_exception:
        raise DownloadAssetException()

    with open(dst, "a") as f:
        f.write(DUMMY_CONTENT_END)
