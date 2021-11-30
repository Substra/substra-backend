import json
import os
from base64 import b64decode
from os import path

import kubernetes
import structlog

from substrapp.utils import list_dir

logger = structlog.get_logger(__name__)

# Chainkeys are used as part of secure aggregation (separate component, absent from this repo)


def prepare_chainkeys_dir(chainkeys_dir: str, compute_plan_tag: str) -> None:
    if os.path.exists(chainkeys_dir) and os.listdir(chainkeys_dir):
        logger.debug(
            "Chainkeys: The folder exists and is non-empty: chainkeys have already been populated.", dir=chainkeys_dir
        )
        return

    _prepare_chainkeys(compute_plan_tag, chainkeys_dir)


def _prepare_chainkeys(compute_plan_tag: str, chainkeys_dir: str) -> None:
    secret_namespace = os.getenv("K8S_SECRET_NAMESPACE", "default")
    label_selector = f"compute_plan={compute_plan_tag}"

    kubernetes.config.load_incluster_config()
    k8s_client = kubernetes.client.CoreV1Api()

    # fetch secrets and write them to disk
    try:
        secrets = k8s_client.list_namespaced_secret(secret_namespace, label_selector=label_selector)
    except kubernetes.client.rest.ApiException as e:
        logger.error("failed to fetch namespaced secrets", namespace=secret_namespace, selector=label_selector)
        raise e

    secrets = secrets.to_dict()["items"]
    if not secrets:
        raise Exception(f"No secret found using label selector {label_selector}")

    formatted_secrets = {}

    for secret in secrets:
        if secret["data"]:
            formatted_secrets[secret["metadata"]["labels"]["index"]] = list(b64decode(secret["data"]["key"]))
        else:
            raise Exception(f'Secret {secret["metadata"]["name"]} does not contain any data')

    with open(path.join(chainkeys_dir, "chainkeys.json"), "w") as f:
        json.dump({"chain_keys": formatted_secrets}, f)
        f.write("\n")  # Add newline cause Py JSON does not

    # remove secrets:
    # do not delete secrets as a running k8s operator will recreate them, instead
    # replace each secret data with an empty dict
    for secret in secrets:
        try:
            k8s_client.replace_namespaced_secret(
                secret["metadata"]["name"],
                secret_namespace,
                body=kubernetes.client.V1Secret(
                    data={},
                    metadata=kubernetes.client.V1ObjectMeta(
                        name=secret["metadata"]["name"],
                        labels=secret["metadata"]["labels"],
                    ),
                ),
            )
        except kubernetes.client.rest.ApiException as e:
            logger.error("failed to remove secrets from namespace", namespace=secret_namespace)
            raise e
    else:
        logger.info(f"{len(secrets)} secrets have been removed")

    logger.info(f"Prepared chainkeys: {list_dir(chainkeys_dir)}")
