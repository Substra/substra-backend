import pathlib

import pytest
from pytest_mock import MockerFixture

import orchestrator
from substrapp.compute_tasks import errors as compute_task_errors
from substrapp.compute_tasks import image_builder
from substrapp.compute_tasks import utils

_VALID_DOCKERFILE = """
FROM ubuntu:16.04
RUN echo "Hello world"
ENTRYPOINT ["python3", "myalgo.py"]
"""
_NO_ENTRYPOINT = """
FROM ubuntu:16.04
"""
_ENTRYPOINT_SHELL_FORM = """
FROM ubuntu:16.04
ENTRYPOINT python3 myalgo.py
"""


class TestBuildImageIfMissing:
    def test_image_already_exists(self, mocker: MockerFixture, algo: orchestrator.Algo):
        ds = mocker.Mock()
        m_container_image_exists = mocker.patch(
            "substrapp.compute_tasks.image_builder.container_image_exists", return_value=True
        )
        algo_image_tag = utils.container_image_tag_from_algo(algo)

        image_builder.build_image_if_missing(datastore=ds, algo=algo)

        m_container_image_exists.assert_called_once_with(algo_image_tag)

    def test_image_build_needed(self, mocker: MockerFixture, algo: orchestrator.Algo):
        ds = mocker.Mock()
        m_container_image_exists = mocker.patch(
            "substrapp.compute_tasks.image_builder.container_image_exists", return_value=False
        )
        m_build_asset_image = mocker.patch("substrapp.compute_tasks.image_builder._build_asset_image")
        algo_image_tag = utils.container_image_tag_from_algo(algo)

        image_builder.build_image_if_missing(datastore=ds, algo=algo)

        m_container_image_exists.assert_called_once_with(algo_image_tag)
        m_build_asset_image.assert_called_once()
        assert m_build_asset_image.call_args.args[1] == algo


class TestGetEntrypointFromDockerfile:
    def test_valid_dockerfile(self, tmp_path: pathlib.Path):
        dockerfile_path = tmp_path / "Dockerfile"
        dockerfile_path.write_text(_VALID_DOCKERFILE)
        entrypoint = image_builder._get_entrypoint_from_dockerfile(str(tmp_path))

        assert entrypoint == ["python3", "myalgo.py"]

    @pytest.mark.parametrize(
        "dockerfile,expected_exc_content",
        [
            pytest.param(_NO_ENTRYPOINT, "Invalid Dockerfile: Cannot find ENTRYPOINT", id="no entrypoint"),
            pytest.param(_ENTRYPOINT_SHELL_FORM, "Invalid ENTRYPOINT", id="shell form"),
        ],
    )
    def test_invalid_dockerfile(self, tmp_path: pathlib.Path, dockerfile: str, expected_exc_content: str):
        dockerfile_path = tmp_path / "Dockerfile"
        dockerfile_path.write_text(dockerfile)

        with pytest.raises(compute_task_errors.BuildError) as exc:
            image_builder._get_entrypoint_from_dockerfile(str(tmp_path))

        assert expected_exc_content in str(exc.value)
