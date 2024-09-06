import pathlib

import pytest
from pytest_mock import MockerFixture

import orchestrator
from api.models import ComputePlan
from builder.exceptions import BuildError
from builder.exceptions import BuildRetryError
from builder.exceptions import PodTimeoutError
from builder.image_builder import image_builder
from substrapp.compute_tasks import utils

_VALID_DOCKERFILE = """
FROM ubuntu:16.04
RUN echo "Hello world"
ENTRYPOINT ["python3", "myfunction.py"]
"""
_NO_ENTRYPOINT = """
FROM ubuntu:16.04
"""
_ENTRYPOINT_SHELL_FORM = """
FROM ubuntu:16.04
ENTRYPOINT python3 myfunction.py
"""


def test_build_image_if_missing_image_already_exists(mocker: MockerFixture, function: orchestrator.Function):
    m_container_image_exists = mocker.patch("builder.docker.container_image_exists", return_value=True)
    function_image_tag = utils.container_image_tag_from_function(function)

    image_builder.build_image_if_missing(channel="channel", function=function)

    m_container_image_exists.assert_called_once_with(function_image_tag)


@pytest.mark.django_db
def test_build_image_if_missing_image_build_needed(mocker: MockerFixture, function: orchestrator.Function):
    m_container_image_exists = mocker.patch("builder.docker.container_image_exists", return_value=False)
    m_datastore = mocker.patch("substrapp.compute_tasks.datastore.Datastore")
    m_build_function_image = mocker.patch("builder.image_builder.image_builder._build_function_image")
    function_image_tag = utils.container_image_tag_from_function(function)

    image_builder.build_image_if_missing(channel="channel", function=function)

    m_datastore.assert_called_once()
    m_container_image_exists.assert_called_once_with(function_image_tag)
    m_build_function_image.assert_called_once()
    assert m_build_function_image.call_args.args[1] == function


def test__build_container_image_podtimeouterror(mocker: MockerFixture) -> None:
    mocker.patch("kubernetes.config.load_incluster_config")
    mocker.patch("builder.image_builder.image_builder._assert_dockerfile_exist")
    mocker.patch("builder.image_builder.image_builder.pod_exists", return_value=True)
    watch_pod = mocker.patch("builder.image_builder.image_builder.watch_pod", side_effect=PodTimeoutError())

    with pytest.raises(BuildRetryError):
        image_builder._build_container_image("path", "name")

    watch_pod.assert_called_once()


def test_get_entrypoint_from_dockerfile_valid_dockerfile(tmp_path: pathlib.Path):
    dockerfile_path = tmp_path / "Dockerfile"
    dockerfile_path.write_text(_VALID_DOCKERFILE)
    entrypoint = image_builder._get_entrypoint_from_dockerfile(str(tmp_path))

    assert entrypoint == ["python3", "myfunction.py"]


@pytest.mark.parametrize(
    "dockerfile,expected_exc_content",
    [
        pytest.param(_NO_ENTRYPOINT, "Invalid Dockerfile: Cannot find ENTRYPOINT", id="no entrypoint"),
        pytest.param(_ENTRYPOINT_SHELL_FORM, "Invalid ENTRYPOINT", id="shell form"),
    ],
)
def test_get_entrypoint_from_dockerfile_invalid_dockerfile(
    tmp_path: pathlib.Path, dockerfile: str, expected_exc_content: str
):
    dockerfile_path = tmp_path / "Dockerfile"
    dockerfile_path.write_text(dockerfile)

    with pytest.raises(BuildError) as exc:
        image_builder._get_entrypoint_from_dockerfile(str(tmp_path))

    assert expected_exc_content in bytes.decode(exc.value.logs.read())


@pytest.mark.parametrize(
    ["statuses", "expected_result"],
    [
        ([], True),
        ([ComputePlan.Status.PLAN_STATUS_DONE.value], True),
        ([ComputePlan.Status.PLAN_STATUS_FAILED.value, ComputePlan.Status.PLAN_STATUS_CANCELED.value], False),
        (
            [
                ComputePlan.Status.PLAN_STATUS_DONE.value,
                ComputePlan.Status.PLAN_STATUS_FAILED.value,
                ComputePlan.Status.PLAN_STATUS_CANCELED.value,
            ],
            True,
        ),
    ],
    ids=["no cp", "done cp", "failed + canceled cp", "done + failed + canceled cp"],
)
def test_check_function_is_runnable(mocker: MockerFixture, statuses: str, expected_result: bool) -> None:
    function_key = "key"
    channel_name = "channel_name"
    compute_plan_getter = mocker.patch("builder.image_builder.image_builder.ComputePlan.objects.filter")
    compute_plan_getter.return_value.values_list.return_value.distinct.return_value = statuses
    result = image_builder.check_function_is_runnable(function_key=function_key, channel_name=channel_name)

    assert result == expected_result
    compute_plan_getter.assert_called_once_with(compute_tasks__function__key=function_key, channel=channel_name)
