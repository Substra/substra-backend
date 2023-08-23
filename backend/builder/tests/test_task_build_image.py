import pytest

from builder.exceptions import BuildError
from substrapp.utils.errors import store_failure


@pytest.mark.django_db
def test_store_failure_build_error():
    asset_key = "42ff54eb-f4de-43b2-a1a0-a9f4c5f4737f"
    msg = "Error building image"
    exc = BuildError(msg)

    failure_report = store_failure(exc=exc, asset_key=asset_key, asset_type="FUNCTION")
    failure_report.refresh_from_db()

    assert str(failure_report.compute_task_key) == asset_key
    assert failure_report.logs.read() == str.encode(msg)
