import pytest

from substrapp.compute_tasks.errors import InvalidContextError


def test_using_archived_datamanager_raises(archived_datamanager_task_input_context):
    """Ensure using an archived datamanager in a compute task will raise an invalid context error"""
    with pytest.raises(InvalidContextError):
        archived_datamanager_task_input_context.data_manager()
