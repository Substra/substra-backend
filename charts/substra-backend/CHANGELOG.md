# Changelog


## [24.3.1] - 2024-03-06

### Fixed

- increased timout in `wait-minio` & changed initContainers order

## [24.3.0] - 2024-03-05

### Removed

- kaniko cache warmer and associated configuration on the worker

## [24.2.1] - 2024-03-01

### Changed

- Bump `bitnami/redis` and `bitnami/common` chart version to `18.17.0` and `2.16.1` respectively

## [24.2.0] - 2024-02-29

## Added

- `privateCa.image.pullSecrets` field added to precise secrets to pull the Docker image.

## Changed

- The default value of `privateCa.image.repository` is changed to the `substra/substra-backend-ca-cert-injector`

## Removed

- `privateCa.image.apkAdd` field removed

## [24.1.0] - 2024-02-29

### Added

- Minio is optional. S3 bucket is now available through LocalStack

## [24.0.3] - 2024-02-26

### Changed

- Update substra-backend image to `0.43.0`

## [24.0.1] - 2023-12-15

### Changed

- Rename `LEDGER_CHANNEL` to `CHANNELS` and `LEDGER_MSP_ID` to `MSP_ID`

## [24.0.0] - 2023-10-16

### Added

- Builder service

## [23.0.2] - 2023-10-18

### Changed

- Update substra-backend image to `0.42.2`

##  [23.0.1] - 2023-10-11

### Changed

- `add-ca-cert` `initContainer`  refactored as Helm helper template
- `wait-init-migrations` `initContainer` refactored to Helm helper template

## [23.0.0] - 2023-10-10

## Added

- `bitnami/common` dependency added

## Changed

- `redis` subchart version incremented to `18.1.2`
- BREAKING: `postgresql` subchart version incremented to `13.1.2`
- `docker-registry` subchart version incremented to `2.2.2`
- `minio` subchart version incremented to `12.0.12`

## [22.8.6] - 2023-10-10

## Added

- Environment variables added to the `wait-postgresql` Helm helper template

## [22.8.5] - 2023-10-09

### Changed

- initContainer `wait-postgresql` refactored to Helm Helper templates

## [22.8.4] - 2023-10-06

## Changed

- `wait-minio` container definition moved to the Helm helper templates

## [22.8.3] - 2023-10-06

### Changed

- Update substra-backend image to `0.42.1`

## [22.8.2] - 2023-09-08

### Changed

- Update substra-backend image to `0.42.0`

## [22.8.1] - 2023-09-07

### Changed

- Update substra-backend image to `0.41.0`

## [22.8.0] - 2023-08-16

### Added

- New `server.allowImplicitLogin` field, controlling whether "implicit login" (`Client.login` in the Substra SDK) is enabled

## [22.7.1] - 2023-08-16

### Changed

- Created role no longer request superfluous permissions

## [22.7.0] - 2023-08-14

### Changed

- Components now avoid writing on the root file system, allowing this chart to run under `readOnlyRootFilesystem: true`
- A secret formerly generated at runtime (`SECRET_KEY`) is now generated at install time and stored in a new secret, fixing issues where this secret would change on application restart

### Fixed

- Missing dash in some created Kubernetes objects

## [22.6.1] - 2023-07-25

### Changed

- Update substra-backend image tag to `0.40.0`

## [22.6.0] - 2023-07-18

### Added

- New `oidc.users.requireApproval` field, that triggers the User Awaiting Approval functionality ([#680](https://github.com/Substra/substra-backend/pull/680))

## [22.5.2] - 2023-06-27

### Changed

- Update substra-backend image tag to `0.39.0`

## 22.5.1

### Changed

- Update substra-backend image tag to `0.38.0`

## [22.5.0] - 2023-06-07

### Added

- allow using an external database in standalone mode through the `database` key in the values ([#658](https://github.com/Substra/substra-backend/pull/658))

## 22.4.4

### Changed

- Update substra-backend image tag to `0.37.0`

## 22.4.3

### Changed

- Update substra-backend image tag to `0.36.1`

## 22.4.2

### Changed

- Update substra-backend image tag to `0.36.0`

## 22.4.1

### Fixed

- Fix OIDC values resulting in invalid manifests in some cases

## 22.4.0

### Added

- Add a new `oidc` field, allowing SSO through OpenID Connect.

## 22.3.4

### Changed

- Make backend image tags default to the chart `appVersion`, and set it to `null` in the default values

## 22.3.3

### Changed

- Update substra-backend image tag to `0.35.1`

## 22.3.2

### Changed

- Update substra-backend image tag to `0.35.0`

## 22.3.1

### Changed

- Update chart maintainers

## 22.3.0

### Added

- New `server.persistence.servermedias.existingClaim` option

## 22.2.4

### Changed

- Update substra-backend image tag to `0.34.1`

## 22.2.3

### Changed

- Update substra-backend image tag to `0.34.0`

## 22.2.2

### Changed

- Update substra-backend image tag to `0.33.0`

## 22.2.1

### Changed

- Update substra-backend image tag to `0.32.0`

## 22.2.0

### Change

- Enable Redis persistence using append-only file (AOF)

## 22.1.3

### Fixed

- ingressClassName is now set correctly on the ingress.

## 22.1.2

### Changed

- Update substra-backend image tag to `0.31.0`

## 22.1.1

### Changed

- Update substra-backend image tag to `0.30.0`

## 22.1.0

### Changed

- Split compute engine and localrep events consumers

## 22.0.3

### Changed

- Update substra-backend image tag to `0.29.0`

## 22.0.2

### Changed

- Fix typos

## 22.0.1

### Changed

- Update image registry

## 22.0.0

### Changed

- BREAKING CHANGE Use Redis instead of RabbitMQ as celery message broker

## 21.1.7

### Changed

- Update `addAccountOperator.users` doc

## 21.1.6

### Fixed

- Fix duplicate `app.kubernetes.io/instance`

## 21.1.5

### Changed

- Update substra-backend image tag to `0.28.0`

## 21.1.4

### Fixed

- Added image pull secrets to migrations job

## 21.1.3

### Changed

- Update substra-backend image tag to 0.27.0

## 21.1.2

### Changed

- Update substra-backend image tag to `0.26.0`

## 21.1.1

### Changed

- Update substra-backend image tag to `0.25.0`

## 21.1.0

### Removed

- settings for orchestrator rabbitmq

## 21.0.2

### Changed

- Update substra-backend image tag to `0.24.0`

## 21.0.1

### Changed

- Update substra-backend image tag to `0.23.1`

## 21.0.0

### Removed

- value disabling postgresql persistence.

## 20.0.0

### Changed

- Update substra-backend image tag to `0.23.0`

## 19.0.0

### Changed

- BREAKING: the format of `image.pullSecrets`, to match that of other Substra charts

## 18.3.1

### Fixed

- Properly reload workers statefulset on secret change

## 18.3.0

### Added

- Auto reload pod on configmap and secret change

## 18.2.0

### Changed

- Run migrations in a _Job_

## 18.1.0

This release contains a breaking change check the UPGRADE document for the upgrade procedure.

### Changed

- BREAKING CHANGE Rename node to organization

## 18.0.0

### Changed

- Dependencies versions for MinIO, RabbitMQ and PostgreSQL including major bumps. If you set specific values for these subcharts adapt them to the newer version.

## 17.3.0

### Added

- Readiness probe for the event app

## 17.2.1

### Changed

- Dependencies versions for minIO, RabbitMQ and PostgreSQL

## 17.2.0

### Added

- Support for ServiceMonitor resource creation directly from the chart

## 17.1.6

### Changed

- Run the loop responsible for adding accounts and running migrations once per 30 min instead of every minute.

## 17.1.5

### Changed

- `google-container/pause` image updated to `gcr.io/google-containers/pause:3.2`, fixes incompatibilities on arm64 architecture

## 17.1.4

### Changed

- `kaniko` image updated to `gcr.io/kaniko-project/executor:v1.8.1`

## 17.1.3

### Fixed

- `kaniko` image is now `gcr.io/kaniko-project/executor:v1.6.0`

## 17.1.2

### Fixed

- Incorrect pod selector in compute pods `NetworkPolicy`

## 17.1.1

### Changed

- `kaniko` image is now `gcr.io/kaniko-project/executor:v1.8.1`

## 17.1.0

### Added

- Exposition of metrics from Celery when metrics are enabled

## 17.0.0

### Changed

- (BREAKING) Event app command changed and is only compatible with images >0.9.0

### Removed

- uwsgi configmap for event app

## 16.2.0

###  Added

- Add lazy-apps to the uWSGI config
- Exposed Django metrics behind the flag `server.metrics`

## 16.1.1

### Changed

- removed duplicate label `app.kubernetes.io/instance` to fix deployment with Flux

## 16.1.0

### Added

- boolean `enabled` fields for event, worker, schedulers services

## 16.0.2

### Changed

- Increase the number of threads on uWSGI to 10

## 16.0.1

### Fixed

- Condition for the worker Service Account

## 16.0.0

### Added

- Use a separate serviceAccount for the event app to limit permissions scope

### Changed

- Renamed the key `worker.rbac.enable` to `worker.rbac.create`

## 15.0.3

### Added

- Add label selectors to servermedias PVCs if `DataSampleStorageInServerMedia` is `true`

## 15.0.2

### Added

- Set `need-app = true` in event app uwsgi configuration

## 15.0.1

### Added

- `configMapRef` `-orchestrator` to the `deployment-server` containers: `init-collect-static` and `init-migrate`
- `configMapRef` `-orchestrator` to the `deployment-events` containers: `wait-init-migrations`

## 15.0.0

### Changed

- update minio to latest version
- update postgresql to latest version
- update rabbitmq to latest version

## 14.0.2

### Added

- `wait-init-migrations configmap` with `wait-init-migrations.sh` to check that there are no pending migration to run.
- `wait-init-migrations init container` in the event app deployment.

## 14.0.1

### Fixed

- Do not create a _PodSecurityPolicy_ if kube version `>=1.25` and add a warning to the README

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
  3. `{{ .Values.organization.name }}.broadcast` broadcast shared across the workers
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

- The pvc `datasamples`, `models`, `computeplan` and `local`

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

## 1.6.0

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
