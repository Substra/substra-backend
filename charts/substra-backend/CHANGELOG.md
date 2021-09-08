# Changelog

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
