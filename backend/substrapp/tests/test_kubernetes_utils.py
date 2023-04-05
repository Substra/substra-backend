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
