import pickle

from substrapp.tasks.tasks_asset_failure_report import FailedAssetKind
from substrapp.tasks.tasks_asset_failure_report import store_asset_failure_report


def test_store_asset_failure_report_success():
    exception_pickled = pickle.dumps(Exception())
    store_asset_failure_report(
        asset_key="",
        asset_type=FailedAssetKind.FAILED_ASSET_COMPUTE_TASK,
        channel_name=None,
        exception_pickled=exception_pickled,
    )
