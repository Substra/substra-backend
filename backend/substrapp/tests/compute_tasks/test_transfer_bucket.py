from substrapp.compute_tasks import transfer_bucket
from substrapp.compute_tasks.context import Context


def test_metadata_generation(testtuple_context: Context):
    metadata = transfer_bucket._generate_metadata(testtuple_context)

    assert metadata["metrics"]["fca0f83f-381e-4a2a-ab54-d009fb00b4af"]["key"] == "fca0f83f-381e-4a2a-ab54-d009fb00b4af"
    for key in "task", "compute_plan", "dataset_name", "metrics":
        assert key in list(metadata.keys())
