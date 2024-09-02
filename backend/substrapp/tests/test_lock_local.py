from pathlib import Path

import pytest

from substrapp import lock_local


# Test that `lock_local.lock_resource() returns the correct excception
def test_lock_local_timeout():
    resource_type = "test"
    unique_identifier = "1"
    # Create fake lock
    slug = f"{resource_type}_{unique_identifier}"
    lock_path = Path(lock_local._get_lock_file_path(slug))
    lock_path.write_text("unique_id")

    with pytest.raises(Exception):
        with lock_local.lock_resource(resource_type, unique_identifier, timeout=1):
            pass
