# Changelog

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
