from unittest import mock

import kubernetes
import pytest
from pytest_mock import MockerFixture

from builder.exceptions import PodTimeoutError
from builder.kubernetes import ObjectState
from builder.kubernetes import PodState
from builder.kubernetes import get_pod_logs
from builder.kubernetes import watch_pod


def test_get_pod_logs(mocker):
    mocker.patch("kubernetes.client.CoreV1Api.read_namespaced_pod_log", return_value="Super great logs")
    k8s_client = kubernetes.client.CoreV1Api()
    logs = get_pod_logs(k8s_client, "pod_name", "container_name", ignore_pod_not_found=True)
    assert logs == "Super great logs"


def test_get_pod_logs_not_found():
    with mock.patch("kubernetes.client.CoreV1Api.read_namespaced_pod_log") as read_pod:
        read_pod.side_effect = kubernetes.client.ApiException(404, "Not Found")
        k8s_client = kubernetes.client.CoreV1Api()
        logs = get_pod_logs(k8s_client, "pod_name", "container_name", ignore_pod_not_found=True)
        assert "Pod not found" in logs


def test_get_pod_logs_bad_request():
    with mock.patch("kubernetes.client.CoreV1Api.read_namespaced_pod_log") as read_pod:
        read_pod.side_effect = kubernetes.client.ApiException(400, "Bad Request")
        k8s_client = kubernetes.client.CoreV1Api()
        logs = get_pod_logs(k8s_client, "pod_name", "container_name", ignore_pod_not_found=True)
        assert "pod_name" in logs


def test_pod_pending_too_long(mocker: MockerFixture) -> None:
    k8s_client = None
    pod_name = "unused"
    retrieve_pod_status = mocker.patch("builder.kubernetes.retrieve_pod_status")
    mocker.patch("builder.kubernetes._get_pod_state", return_value=PodState(ObjectState.PENDING))
    mocker.patch("builder.kubernetes.BUILDER_KANIKO_STARTUP_MAX_ATTEMPTS", new=1)

    with pytest.raises(PodTimeoutError):
        watch_pod(k8s_client, pod_name)

    retrieve_pod_status.assert_called_once_with(k8s_client, pod_name)
