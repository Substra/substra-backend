import pytest

from substrapp.views.filters_utils import get_filters


@pytest.mark.parametrize(
    ("raw_filters", "parsed_filters"),
    (
        (
            "algo:name:algo1",
            [
                {
                    "algo": {
                        "name": ["algo1"],
                    },
                },
            ],
        ),
        (
            "algo:name:algo1,algo:owner:owner1",
            [
                {
                    "algo": {
                        "name": ["algo1"],
                        "owner": ["owner1"],
                    },
                },
            ],
        ),
        (
            "algo:name:algo1,algo:name:algo2",
            [
                {
                    "algo": {
                        "name": ["algo1", "algo2"],
                    },
                },
            ],
        ),
        (
            "algo:name:algo1-OR-algo:owner:owner1",
            [
                {
                    "algo": {
                        "name": ["algo1"],
                    },
                },
                {
                    "algo": {
                        "owner": ["owner1"],
                    },
                },
            ],
        ),
    ),
)
def test_get_filters_simple(raw_filters, parsed_filters):
    assert get_filters(raw_filters) == parsed_filters
