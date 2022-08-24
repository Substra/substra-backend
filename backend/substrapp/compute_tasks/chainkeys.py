import json
import os
from base64 import b64decode
from os import path

import structlog
from django.conf import settings
from kubernetes import client as k8s
from kubernetes import config as k8s_config

from substrapp.utils import list_dir

logger = structlog.get_logger(__name__)

# Chainkeys are used as part of secure aggregation (separate component, absent from this repo)

SECRET_NAMESPACE = settings.K8S_SECRET_NAMESPACE
CHAINKEYS_FILENAME = "chainkeys.json"

Chainkeys = dict[str, list[bytes]]


class ChainkeysPreparationError(Exception):
    pass


def prepare_chainkeys_dir(chainkeys_dir: str, compute_plan_tag: str) -> None:
    if os.path.exists(chainkeys_dir) and os.listdir(chainkeys_dir):
        logger.debug(
            "Chainkeys: The folder exists and is non-empty: chainkeys have already been populated.", dir=chainkeys_dir
        )
    else:
        _prepare_chainkeys(chainkeys_dir, compute_plan_tag)


def _prepare_chainkeys(chainkeys_dir: str, compute_plan_tag: str) -> None:
    label_selector = f"compute_plan={compute_plan_tag}"

    secrets = _retrieve_secrets(label_selector)

    if not secrets:
        raise ChainkeysPreparationError(f"No secret found using label selector {label_selector}")

    chainkeys = _extract_chainkeys(secrets)

    _write_chainkeys(chainkeys_dir, chainkeys)
    _clear_secrets(secrets)

    logger.info("Prepared chainkeys", dir=list_dir(chainkeys_dir))


def _retrieve_secrets(label_selector: str) -> list[k8s.V1Secret]:
    k8s_config.load_incluster_config()
    k8s_client = k8s.CoreV1Api()

    try:
        secrets: k8s.V1SecretList = k8s_client.list_namespaced_secret(SECRET_NAMESPACE, label_selector=label_selector)
    except k8s.ApiException as apiexc:
        raise ChainkeysPreparationError(
            f"Failed to fetch secrets from cluster in namespace {SECRET_NAMESPACE} with selector {label_selector}"
        ) from apiexc

    return secrets.items


def _extract_chainkeys(secrets: list[k8s.V1Secret]) -> Chainkeys:
    chainkeys = {}

    for secret in secrets:
        if secret.data:
            chainkeys[secret.metadata.labels["index"]] = list(b64decode(secret.data["key"]))
        else:
            raise ChainkeysPreparationError(f"Secret {secret.metadata.name} does not contain any data")

    return chainkeys


def _write_chainkeys(chainkeys_dir: str, chainkeys: Chainkeys) -> None:
    with open(path.join(chainkeys_dir, CHAINKEYS_FILENAME), "w") as f:
        json.dump({"chain_keys": chainkeys}, f)
        f.write("\n")  # Add newline cause Py JSON does not


def _clear_secrets(secrets: list[k8s.V1Secret]) -> None:
    """clear the Kubernetes secrets to avoid reusing the chainkeys.

    Do not delete secrets as a running k8s operator will recreate them, instead
    replace each secret data with an empty dict
    """
    k8s_config.load_incluster_config()
    k8s_client = k8s.CoreV1Api()

    for secret in secrets:
        try:
            k8s_client.replace_namespaced_secret(
                secret.metadata.name,
                SECRET_NAMESPACE,
                body=k8s.V1Secret(
                    data={},
                    metadata=k8s.V1ObjectMeta(
                        name=secret.metadata.name,
                        labels=secret.metadata.labels,
                    ),
                ),
            )
        except k8s.ApiException as apiexc:
            raise ChainkeysPreparationError(f"failed to remove secrets from namespace {SECRET_NAMESPACE}") from apiexc
    else:
        logger.info("secrets have been cleared", len=len(secrets))
