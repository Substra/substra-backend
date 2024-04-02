import json
from unittest import mock

import pytest
from kubernetes import client as k8s

from substrapp.compute_tasks.chainkeys import CHAINKEYS_FILENAME
from substrapp.compute_tasks.chainkeys import ChainkeysPreparationError
from substrapp.compute_tasks.chainkeys import prepare_chainkeys_dir


def test_prepare_chainkeys_dir(tmpdir):
    secrets = []
    secrets.append(
        k8s.V1Secret(
            data={"key": "9HI2MVHg98dSxsvJ6cT/3uiSkW3ik56LV5Jqaiy0YRU="},
            metadata=k8s.V1ObjectMeta(labels={"index": "1", "pair": "organization-2", "compute_plan": "cp1"}),
        )
    )
    secrets.append(
        k8s.V1Secret(
            data={"key": "Lx8u1CW6ZVRmj9GmEnAsWKZH7htFGZehW7ta0IJLdzU="},
            metadata=k8s.V1ObjectMeta(labels={"index": "2", "pair": "organization-3", "compute_plan": "cp1"}),
        )
    )
    # fmt: off
    expected_output = {
        "chain_keys": {
            "1": [244, 114, 54, 49, 81, 224, 247, 199, 82, 198, 203, 201, 233, 196, 255, 222, 232, 146, 145, 109, 226, 147, 158, 139, 87, 146, 106, 106, 44, 180, 97, 21],  # noqa: E501
            "2": [47, 31, 46, 212, 37, 186, 101, 84, 102, 143, 209, 166, 18, 112, 44, 88, 166, 71, 238, 27, 69, 25, 151, 161, 91, 187, 90, 208, 130, 75, 119, 53],  # noqa: E501
        }
    }
    # fmt: on

    with (
        mock.patch("substrapp.compute_tasks.chainkeys._retrieve_secrets") as mretrievesecrets,
        mock.patch("substrapp.compute_tasks.chainkeys._clear_secrets") as mcleansecrets,
    ):
        mretrievesecrets.return_value = secrets
        prepare_chainkeys_dir(tmpdir, "cp1")

        with open(tmpdir / CHAINKEYS_FILENAME, "r") as ckfile:
            data = json.load(ckfile)

            assert data == expected_output
        mretrievesecrets.assert_called_once()
        mcleansecrets.assert_called_once()


def test_chainkeys_already_prepared(tmpdir):
    with open(tmpdir / CHAINKEYS_FILENAME, "w") as ckfile:
        ckfile.write("chainkeys")

    with mock.patch("substrapp.compute_tasks.chainkeys._prepare_chainkeys") as mprepareck:
        prepare_chainkeys_dir(tmpdir, "cp1")

        mprepareck.assert_not_called()


def test_no_chainkeys(tmpdir):
    with mock.patch("substrapp.compute_tasks.chainkeys._retrieve_secrets") as mretrievesecrets:
        mretrievesecrets.return_value = []
        with pytest.raises(ChainkeysPreparationError) as excprep:
            prepare_chainkeys_dir(tmpdir, "cp1")

        assert "No secret found" in str(excprep.value)


def test_empty_secret(tmpdir):
    secrets = []
    secrets.append(
        k8s.V1Secret(
            data={},
            metadata=k8s.V1ObjectMeta(
                labels={"index": "1", "pair": "organization-2", "compute_plan": "cp1"}, name="test-secret"
            ),
        )
    )

    with mock.patch("substrapp.compute_tasks.chainkeys._retrieve_secrets") as mretrievesecrets:
        mretrievesecrets.return_value = secrets
        with pytest.raises(ChainkeysPreparationError) as excprep:
            prepare_chainkeys_dir(tmpdir, "cp1")

        assert "does not contain any data" in str(excprep.value)
