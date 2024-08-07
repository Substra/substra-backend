import datetime
import functools

import pytest
from django.test import override_settings
from django.urls.base import reverse
from django.utils.duration import duration_microseconds
from rest_framework import status

import orchestrator
from api.models import ComputeTask
from api.models import FunctionProfilingStep
from api.tests import asset_factory as factory

CHANNEL = "mychannel"
TEST_ORG = "MyTestOrg"

ORG_SETTINGS = {
    "CHANNELS": {"mychannel": {"model_export_enabled": True}},
    "MSP_ID": TEST_ORG,
}

EXTRA = {"HTTP_SUBSTRA_CHANNEL_NAME": CHANNEL, "HTTP_ACCEPT": "application/json;version=0.0"}
TASK_PROFILING_LIST_URL = reverse("api:task_profiling-list")


def _get_profiling_expected_result(key: str):
    return [
        {
            "compute_task_key": str(key),
            "execution_rundown": [],
            "task_duration": None,
        }
    ]


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_task_profiling_list_success(authenticated_client, task_profiling):
    response = authenticated_client.get(TASK_PROFILING_LIST_URL)
    expected_results = _get_profiling_expected_result(task_profiling.compute_task.key)
    assert response.json() == {
        "count": len(expected_results),
        "next": None,
        "previous": None,
        "results": expected_results,
    }


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_task_profiling_list_wrong_channel(authenticated_client, task_profiling):
    authenticated_client.channel = "yourchannel"
    response = authenticated_client.get(TASK_PROFILING_LIST_URL)
    assert response.json() == {"count": 0, "next": None, "previous": None, "results": []}


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_task_profiling_retrieve_success(authenticated_client, task_profiling):
    expected_results = _get_profiling_expected_result(task_profiling.compute_task.key)
    response = authenticated_client.get(
        reverse("api:task_profiling-detail", args=[expected_results[0]["compute_task_key"]]),
    )
    assert response.json() == expected_results[0]


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_task_profiling_create_bad_client(authenticated_client, task_profiling):
    response = authenticated_client.post(
        TASK_PROFILING_LIST_URL, {"compute_task_key": str(task_profiling.compute_task.key), "channel": CHANNEL}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_task_profiling_create_success(authenticated_backend_client, create_compute_task):
    compute_task = create_compute_task(status=ComputeTask.Status.STATUS_EXECUTING)
    response = authenticated_backend_client.post(
        TASK_PROFILING_LIST_URL, {"compute_task_key": str(compute_task.key)}, **EXTRA
    )
    assert response.status_code == status.HTTP_201_CREATED


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_already_exist_task_profiling(authenticated_backend_client):
    function = factory.create_function()
    cp = factory.create_computeplan()
    task = factory.create_computetask(compute_plan=cp, function=function)

    response = authenticated_backend_client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(task.key)})
    assert response.status_code == status.HTTP_201_CREATED

    response = authenticated_backend_client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(task.key)})
    assert response.status_code == status.HTTP_409_CONFLICT


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db(transaction=True)
def test_task_profiling_update_datetime(authenticated_backend_client, create_compute_plan, create_compute_task):
    compute_plan = create_compute_plan()
    compute_task = create_compute_task(compute_plan)

    authenticated_backend_client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(compute_task.key)})
    task_profiling = compute_task.task_profiling
    task_profiling.refresh_from_db()
    previous_datetime = task_profiling.creation_date

    profiling_url = reverse("api:task_profiling-detail", args=[str(compute_task.key)])
    authenticated_backend_client.put(profiling_url, {"compute_task_key": str(compute_task.key)}, **EXTRA)
    task_profiling.refresh_from_db()
    new_datetime = task_profiling.creation_date

    assert new_datetime > previous_datetime


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_task_profiling_add_step(authenticated_backend_client, task_profiling):
    compute_task_key = task_profiling.compute_task.key
    step_url = reverse("api:step-list", args=[str(compute_task_key)])
    response = authenticated_backend_client.post(
        step_url, {"step": "custom_step", "duration": datetime.timedelta(seconds=20)}, **EXTRA
    )
    assert response.status_code == status.HTTP_201_CREATED

    expected_results = [
        {
            "compute_task_key": str(compute_task_key),
            "execution_rundown": [{"duration": 20000000, "step": "custom_step"}],
            "task_duration": None,
        }
    ]

    response = authenticated_backend_client.get(TASK_PROFILING_LIST_URL, **EXTRA)
    assert response.json() == {
        "count": len(expected_results),
        "next": None,
        "previous": None,
        "results": expected_results,
    }


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db()
def test_task_profiling_add_step_no_datetime_change(authenticated_backend_client, task_profiling):
    compute_task_key = task_profiling.compute_task.key
    previous_datetime = task_profiling.creation_date
    step_url = reverse("api:step-list", args=[str(compute_task_key)])
    authenticated_backend_client.post(step_url, {"compute_task_key": str(compute_task_key)})
    task_profiling.refresh_from_db()
    new_datetime = task_profiling.creation_date
    assert new_datetime == previous_datetime


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_already_exist_step(authenticated_backend_client, task_profiling):
    url = reverse("api:step-list", args=[str(task_profiling.compute_task.key)])
    content = {"step": "step name", "duration": datetime.timedelta(seconds=20)}
    response = authenticated_backend_client.post(url, content, **EXTRA)
    assert response.status_code == status.HTTP_201_CREATED

    response = authenticated_backend_client.post(url, content, **EXTRA)
    assert response.status_code == status.HTTP_409_CONFLICT


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db(transaction=True)
def test_step_update(authenticated_backend_client, task_profiling):
    url = reverse("api:step-list", args=[str(task_profiling.compute_task.key)])
    old_duration = datetime.timedelta(seconds=20)
    new_duration = datetime.timedelta(seconds=40)
    content = {"step": "step name", "duration": old_duration}
    assert old_duration != new_duration

    authenticated_backend_client.post(url, content, **EXTRA)
    task_profiling.refresh_from_db()
    step = task_profiling.execution_rundown.first()
    assert step.duration == old_duration

    url = reverse("api:step-detail", args=[str(task_profiling.compute_task.key), content["step"]])
    content["duration"] = new_duration
    response = authenticated_backend_client.put(url, content, **EXTRA)
    assert response.status_code == status.HTTP_200_OK

    step.refresh_from_db()
    assert step.duration == new_duration


@override_settings(**EXTRA)
@override_settings(
    MSP_ID="other_org",
)
@pytest.mark.django_db()
def test_task_profiling_create_fail_other_backend(authenticated_client, create_compute_task):
    task = create_compute_task()

    response = authenticated_client.post(TASK_PROFILING_LIST_URL, {"compute_task_key": str(task.key)})
    assert response.status_code == status.HTTP_403_FORBIDDEN


def _get_serialized_step(step: FunctionProfilingStep) -> dict:
    return {"duration": duration_microseconds(step.duration), "step": step.step.value}


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_function_profiling_get_steps_unfinished(authenticated_client, create_function_profiling):
    function = factory.create_function()
    function_key = function.key

    step = create_function_profiling(function=function, step=orchestrator.FunctionProfilingStep.BUILD_IMAGE)
    step_url = reverse("api:function-profiling-list", args=[str(function_key)])
    response = authenticated_client.get(step_url)

    assert response.status_code == status.HTTP_200_OK

    expected_results = {
        "function_key": str(function_key),
        "execution_rundown": [_get_serialized_step(step)],
        "duration": None,
    }

    assert response.json() == expected_results


@override_settings(**ORG_SETTINGS)
@pytest.mark.django_db
def test_function_profiling_get_steps_finished(authenticated_client, create_function_profiling):
    function = factory.create_function()
    function_key = function.key

    steps = [create_function_profiling(function=function, step=step) for step in orchestrator.FunctionProfilingStep]
    step_url = reverse("api:function-profiling-list", args=[str(function_key)])
    response = authenticated_client.get(step_url)
    print(response.json())
    assert response.status_code == status.HTTP_200_OK

    execution_rundown = [_get_serialized_step(step) for step in steps]
    total_duration = functools.reduce(lambda acc, step: duration_microseconds(step.duration) + acc, steps, 0)
    expected_results = {
        "function_key": str(function_key),
        "execution_rundown": execution_rundown,
        "duration": total_duration,
    }

    assert response.json() == expected_results
