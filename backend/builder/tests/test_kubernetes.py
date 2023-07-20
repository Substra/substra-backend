from unittest import mock

import kubernetes

from builder.kubernetes import get_pod_logs


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
