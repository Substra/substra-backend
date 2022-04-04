
<!-- This file is an auto-generated file, please do not edit manually. Instead you can run `make docs` to update it -->
# Connect setting
This file document all the settings of the connect application

These settings are configured through env variables.
They can be set in the [chart](../charts/substra-backend/README) through the `config` value.

## Global settings

| Setting | Default value |
| ---     | ---           |
| `ALLOWED_HOSTS` | `[]` |
| `BACKEND_VERSION` | `nil` |
| `CELERYBEAT_FLUSH_EXPIRED_TOKENS_TASK_PERIOD` | `24 * 3600` |
| `CELERYBEAT_MAXIMUM_IMAGES_TTL` | `7 * 24 * 3600` |
| `CELERYBEAT_SCHEDULE_TASK_PERIOD` | `3 * 3600` |
| `CELERY_BROKER_HOST` | `localhost` |
| `CELERY_BROKER_PASSWORD` | `nil` |
| `CELERY_BROKER_PORT` | `5672` |
| `CELERY_BROKER_USER` | `nil` |
| `CELERY_TASK_MAX_RETRIES` | `7` |
| `CELERY_TASK_RETRY_BACKOFF` | `60` |
| `CELERY_TASK_RETRY_BACKOFF_MAX` | `64 * 60` |
| `CELERY_WORKER_CONCURRENCY` | `1` |
| `COMMON_HOST_DOMAIN` | `nil` |
| `COMPUTE_POD_FS_GROUP` | `nil` |
| `COMPUTE_POD_GKE_GPUS_LIMITS` | `0` |
| `COMPUTE_POD_RUN_AS_GROUP` | `nil` |
| `COMPUTE_POD_RUN_AS_USER` | `nil` |
| `COMPUTE_POD_STARTUP_TIMEOUT_SECONDS` | `300` |
| `DATA_UPLOAD_MAX_SIZE` | `1024 * 1024 * 1024` |
| `DEBUG_KEEP_POD_AND_DIRS` | `False` |
| `DEBUG_QUICK_IMAGE` | `False` |
| `DJANGO_LOG_SQL_QUERIES` | `True` |
| `ENABLE_DATASAMPLE_STORAGE_IN_SERVERMEDIAS` | `False` |
| `ENABLE_METRICS` | `False` |
| `EXPIRY_TOKEN_LIFETIME` | `24 * 60` |
| `GZIP_MODELS` | `False` |
| `HOST_IP` | `nil` |
| `HTTP_CLIENT_TIMEOUT_SECONDS` | `30` |
| `ISOLATED` | `nil` |
| `K8S_SECRET_NAMESPACE` | `default` |
| `KANIKO_DOCKER_CONFIG_SECRET_NAME` | `nil` |
| `KANIKO_IMAGE` | `nil` |
| `KANIKO_MIRROR` | `False` |
| `LOCALREP_RESYNC_EVENTS_PAGE_SIZE` | `1000` |
| `LOGGING_USE_COLORS` | `True` |
| `LOG_LEVEL` | `INFO` |
| `NAMESPACE` | `nil` |
| `OBJECTSTORE_ACCESSKEY` | `nil` |
| `OBJECTSTORE_SECRETKEY` | `nil` |
| `OBJECTSTORE_URL` | `nil` |
| `PAGINATION_MAX_PAGE_SIZE` | `10000` |
| `POD_IP` | `nil` |
| `REGISTRY` | `nil` |
| `REGISTRY_IS_LOCAL` | `nil` |
| `REGISTRY_PULL_DOMAIN` | `nil` |
| `REGISTRY_SCHEME` | `nil` |
| `REGISTRY_SERVICE_NAME` | `nil` |
| `SUBPATH` | `nil` |
| `TASK_CACHE_DOCKER_IMAGES` | `False` |
| `TASK_CHAINKEYS_ENABLED` | `False` |
| `TASK_LIST_WORKSPACE` | `True` |
| `TOKEN_STRATEGY` | `unique` |
| `WORKER_PVC_DOCKER_CACHE` | `nil` |
| `WORKER_PVC_IS_HOSTPATH` | `nil` |
| `WORKER_PVC_SUBTUPLE` | `nil` |
| `WORKER_REPLICA_SET_NAME` | `nil` |

## Orchestrator settings

| Setting | Default value |
| ---     | ---           |
| `ORCHESTRATOR_HOST` | `nil` |
| `ORCHESTRATOR_MTLS_ENABLED` | `nil` |
| `ORCHESTRATOR_PORT` | `nil` |
| `ORCHESTRATOR_RABBITMQ_AUTH_PASSWORD` | `nil` |
| `ORCHESTRATOR_RABBITMQ_AUTH_USER` | `nil` |
| `ORCHESTRATOR_RABBITMQ_HOST` | `nil` |
| `ORCHESTRATOR_RABBITMQ_PORT` | `nil` |
| `ORCHESTRATOR_RABBITMQ_TLS_CLIENT_CACERT_PATH` | `nil` |
| `ORCHESTRATOR_RABBITMQ_TLS_CLIENT_CERT_PATH` | `nil` |
| `ORCHESTRATOR_RABBITMQ_TLS_CLIENT_KEY_PATH` | `nil` |
| `ORCHESTRATOR_RABBITMQ_TLS_ENABLED` | `nil` |
| `ORCHESTRATOR_TLS_CLIENT_CERT_PATH` | `nil` |
| `ORCHESTRATOR_TLS_CLIENT_KEY_PATH` | `nil` |
| `ORCHESTRATOR_TLS_ENABLED` | `nil` |
| `ORCHESTRATOR_TLS_SERVER_CACERT_PATH` | `nil` |

## Org settings

| Setting | Default value |
| ---     | ---           |
| `BACKEND_DEFAULT_PORT` | `8000` |
| `ORG_NAME` | `nil` |

## CORS settings

| Setting | Default value |
| ---     | ---           |
| `CORS_ALLOW_CREDENTIALS` | `False` |
| `CORS_ORIGIN_WHITELIST` | `[]` |

## Ledger settings

| Setting | Default value |
| ---     | ---           |
| `LEDGER_CHANNELS` | `nil` |
| `LEDGER_MSP_ID` | `nil` |

## Event app settings

| Setting | Default value |
| ---     | ---           |
