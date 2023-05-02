from unittest import mock

import kubernetes
import pytest

import substrapp.exceptions
import substrapp.kubernetes_utils


def test_get_service_node_port():
    with mock.patch("kubernetes.config.load_incluster_config"), mock.patch(
        "kubernetes.client.CoreV1Api.read_namespaced_service"
    ) as mgetservice:
        mgetservice.side_effect = kubernetes.client.ApiException(500, "something happened")

        with pytest.raises(substrapp.exceptions.KubernetesError) as excinfo:
            substrapp.kubernetes_utils.get_service_node_port("my_service")
        assert "Failed to retrieve node port" in str(excinfo.value)

        # Test service not exposed as a node port
        service = kubernetes.client.V1Service(
            spec=kubernetes.client.V1ServiceSpec(
                ports=[kubernetes.client.V1ServicePort(name="test", port=8000, target_port=8000)]
            )
        )
        mgetservice.side_effect = None
        mgetservice.return_value = service

        with pytest.raises(substrapp.exceptions.KubernetesError) as excinfo:
            substrapp.kubernetes_utils.get_service_node_port("my_service")
        assert "Failed to retrieve node port" in str(excinfo.value)

        # Test with a node_port set on the service
        service.spec.ports[0].node_port = 9000
        port = substrapp.kubernetes_utils.get_service_node_port("my_service")
        assert port == 9000


def test_get_pod_logs(mocker):
    mocker.patch("kubernetes.client.CoreV1Api.read_namespaced_pod_log", return_value="Super great logs")
    k8s_client = kubernetes.client.CoreV1Api()
    logs = substrapp.kubernetes_utils.get_pod_logs(k8s_client, "pod_name", "container_name", ignore_pod_not_found=True)
    assert logs == "Super great logs"


def test_get_pod_logs_not_found():
    with mock.patch("kubernetes.client.CoreV1Api.read_namespaced_pod_log") as read_pod:
        read_pod.side_effect = kubernetes.client.ApiException(404, "Not Found")
        k8s_client = kubernetes.client.CoreV1Api()
        logs = substrapp.kubernetes_utils.get_pod_logs(
            k8s_client, "pod_name", "container_name", ignore_pod_not_found=True
        )
        assert "Pod not found" in logs


def test_get_pod_logs_bad_request():
    with mock.patch("kubernetes.client.CoreV1Api.read_namespaced_pod_log") as read_pod:
        read_pod.side_effect = kubernetes.client.ApiException(400, "Bad Request")
        k8s_client = kubernetes.client.CoreV1Api()
        logs = substrapp.kubernetes_utils.get_pod_logs(
            k8s_client, "pod_name", "container_name", ignore_pod_not_found=True
        )
        assert "pod_name" in logs
