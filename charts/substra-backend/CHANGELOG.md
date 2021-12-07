# Changelog

## 14.0.0

Moved algos, datamanagers, and metrics from PVCs to MinIO

### Removed
- `data-algos` volume from the deployment-server
- `data-datamanagers` volume from the deployment-server
- `data-metrics` volume from the deployment-server
- `algo`, `datamanager` and `metrics` pvc removed
- `MEDIA_ROOT` configmap setting

## Added
- `SUBTUPLE_DIR` configmap setting

## 13.0.6

## Added

- `SERVERMEDIAS_ROOT` configmap setting
- update servermedias PVC attributes

## 13.0.5

### Added
- Make server readiness/liveness probe settings configurable

## 13.0.4

### Changed
- Bump postgresql dependency from 10.3.6 to 10.13.0

## 13.0.3

### Removed
- Authorization to access the `node` api with the worker _ServiceAccount_

## 13.0.2

### Changed

- replace `alpine` by `ubuntu` as privateCA init container image

## 13.0.1

### Changed
- The orchestrator cacert is a _ConfigMap_ instead of a _Secret_

## 13.0.0

### Added

- `config` key used to set config environment variables for the backend
- `events.image` values to set the event app container image independently

### Removed
- `gzipModels` value is removed as the default value is already the application default value
- `pagination.maxPageSize` value is removed as the default value is already the application default value
- `BACKEND_DEFAULT_PORT` env variable from the server and events deployment as the default value is the only possible value
- `backend.tokenStrategy` value is removed as the default value is already the application default value
- `peer.mspID` is moved to `orchestrator.mspID` as there is no notion of Hyperledger peer anymore
- `celerybeat.taskPeriod` value is removed as the default value is already the application default value
- `celerybeat.expiredTokensFlushPeriod` value is removed as the default value is already the application default value
- `celerybeat.maximumImagesTTL` value is removed as the default value is already the application default value
- `httpClient.timeoutSeconds` value is removed as the default value is already the application default value
- `backend.compute.registry` value is removed we will use the same registry as the one in `backend.kaniko.image.registry`
- Support for hostpath volumes directly in the chart

### Changed

- Almost all the keys in the Values files were renamed to better fit their actual purposes
- Event app update strategy changed from `Recreate` to default (`RollingUpdate`)

## 12.1.1
### Fixed

- Graceful shutdown of add-account-operator

## 12.1.0
### Added
- Optional `backend.subpath` setting to serve the API under a subpath

## 12.0.5
### Changed
- rename celery specific env variable

## 12.0.4
### Changed

- Kaniko prepopulate job can use `dstImage` to configure the repo name in the local private registry

## 12.0.3
### Changed

- Substra backend service type is now `ClusterIP` instead of `NodePort` by default as it's more secure to keep traffic internal by default.

## 12.0.2

### Changed
- Open stdin to enable debugger (dev only).

## 12.0.1

### Changed
- updated chart logo

## 12.0.0

### Changed
- (BREAKING) Replace pvc name objectives by metrics

## 11.0.0

See [UPGRADE.md](./UPGRADE.md#11.0.0)

### Added
- `deleteWorkerPvc` added
- `worker pods` are controlled by a `statefulset` (previously by a `deployment`)
- each `celeryWorker` instance is listening to 3 queues:
  1. `{{ .Values.organization.name }}.worker` generic shared worker queue
  2. `{{ .Values.organization.name }}.worker-${HOSTNAME##*-}` worker specific queue
  3. `{{ .Values.organization.name }}.broadcast` broadcast shared accross the workers
- Optional skaffold profile: [preferred](../../examples/values/spread_workers.yaml) `antiAffinity` to schedule 1 worker pod per namespace

### Changed
- `Kaniko cache warming` is performed in each `worker pod` instead of a separate pod

## 10.0.0

### Changed
- `docker-cache` pvc is now configurable in the values file (under `backend.kaniko.persistence`)

## 9.0.0

See [UPGRADE.md](./UPGRADE.md#9.0.0)

### Changed
- `subtuple` pvc is `worker`-only (not `server` anymore)
- `algos`, `aggregatealgos`, `compositealgos`, `datamanagers` and `objectives` pvcs are `server`-only (not `worker` anymore)

### Added
- Add an `objectstore` deployment / service (minio)
- Add `celeryworker.persistence.servermedias.enableDatasampleStorage`

### Removed
- The pvc `datasamples`, `models`,  `computeplan` and `local`

## 8.0.0

### Changed
- `backend.commonHostDomain` is now required to ensure cookies set by the backend will be returned by the frontend.

  It must contain the common part of the frontend and backend domain.

  E.g. `substra-frontend.node-1.com` / `substra-backend.node-1.com` -> `COMMON_HOST_DOMAIN=node-1.com`

## 7.0.0

### Removed
- removed unused aggregatealgos and compositealgos volumes

## 6.0.0

### Changed
- Change docker-registry helm chart from stable deprecated for twuni maintained

## 5.0.1

### Added
- Support for 1.19.x pre-releases

## 5.0.0

### Added
- support for Kubernetes 1.22

### Changed
- Ingress values definitions

### Removed
- support for Kubernetes versions <= 1.19.0

## 4.0.0

### Changed
- updated rabbitmq dependency chart
- updated postgresql dependency chart
- `rabbitmq.host` to target a custom rabbitmq host
- `rabbitmq.auth.user` to `rabbitmq.auth.username` to match the rabbitmq chart values structure
- remove ledger configuration

### Added
- support for subchart fullnameOverride
- support orchestrator connection configuration (grpc + rabbitmq)

## 3.3.1

### Fixed
- Fixed kaniko cache warmer

## 3.3.0

### Added
- Add `PAGINATION_MAX_PAGE_SIZE` configuration to backend chart

## 3.2.0

### Added

- Helm hook to delete remaining compute pods after application deletion

## 3.1.0

### Added
- Add podStartupTimeoutSeconds value under compute field to define the maximum time to wait for a compute pod to start in seconds

## 3.0.0

### Changed
- Bump rabbitmq chart to 8.16.2 (see [UPGRADE.md](./UPGRADE.md))


## 2.3.0

### Added
- Add dockerConfigSecretName value under kaniko field to allow its builder to fetch images from private repository


## 2.2.1

### Added
- Add DJANGO_ALLOW_ASYNC_UNSAFE=true in event app deployment

## 2.2.0

### Added
- Add pod execution permission in RBAC

### Changed
- Updated NetworkPolicy matchLabels

### Removed
- Unused `CELERYWORKER_IMAGE` env variable


## 2.1.0

### Added
- Add new celerybeat configuration setting `maximumImagesTTL`, which will be the image lifetime in the local docker registry
- Fix deployment for celerybeat and celeryscheduler
- Set extra env `TASK_CACHE_DOCKER_IMAGES` to `'True'` by default

## 2.0.4

### Changed
- `kaniko` image is now `gcr.io/kaniko-project/executor:v1.6.0`


## 2.0.3

### Added
- Add new channel configuration setting `model_export_enabled`. When enabled, it allows authenticated users to download models trained on the current node.

## 2.0.2

- fix `service.port` incorrectly used in uwsgi configuration

## 2.0.1

### Added
- new `celerybeat.expiredTokensFlushPeriod` option

## 2.0.0

### Changed

- Docker registry `NodePort` port is now auto-allocated:
  - Remove `docker-registry.service.nodePort` (previously set to `32000`)
  - Removed port number from `registry.pullDomain` (previously set to `127.0.0.1:32000`)

## 1.9.2

### Changed
- Add pod and host ip value to backend-server deployment as environment variables

## 1.9.1

### Changed
- `docker-registry` default service value to nodePort


## 1.9.0

### Changed
- `kaniko` image is now `gcr.io/kaniko-project/executor:v1.3.0`


## 1.8.0

### Changed
- `persistence.volumes` is now an object instead of an array
- `persistence.volumes[].name` is now the key of the volume object

## 1.7.0

### Changed
- Refactor of the kubernetes objects labels

## 1.6.0

- Refactor `channels` and `chaincodes` values

## 1.5.0

- Refactor Hyperledger Fabric settings. Introduce `substra-backend-ledger` ConfigMap.

## 1.4.0

- Consolidate docker images into a unique `substrafoundation/substra-backend` image

## 1.3.1

- Remove unused `flower` deployment/service

## 1.2.1

- Mount `/var/substra/local` in Read-Write mode in the worker pod

## 1.2.0

- Added a new deployment: `substra-backend-events`

## 1.1.4

- `celerybeat` and `celeryworker` docker images are replaced by a unique `celery` image

## 1.1.3

- Bumped kaniko to `v1.0.0`
- Added `backend.kaniko.cache.warmer.image`
- Added `backend.kaniko.cache.warmer.images` (replaces `prePulledImages`)
- By default, don't warm up kaniko cache
- By default, don't prepopulate local docker registry

## 1.1.2

- Added `httpClient.timeoutSeconds`

## 1.1.1

- Added `backend.grpc.keepalive.timeMs`

## 1.1.0

- `channel` (scalar type) is replaced with `channels` (list type)
- Added `users[].channel` (required field)
