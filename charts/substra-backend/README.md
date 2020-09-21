# Substra Backend

Substra Backend is a component of [Substra](https://github.com/SubstraFoundation/substra).

## Prerequisites

- Kubernetes 1.14+
- If you want to enable GPU support, install the nvidia device plugin for kubernetes: https://github.com/NVIDIA/k8s-device-plugin or https://github.com/NVIDIA/gpu-operator

## Changelog

See [CHANGELOG.md](./CHANGELOG.md)

## Configuration

The following table lists the configurable parameters of the substra-backend chart and default values.

:warning: This list is a work in progress. Please refer to [values.yaml](./values.yaml) for full configuration options.

| Parameter                          | Description                                     | Default                                                    |
| ---------------------------------- | ------------------------------------------------ | ---------------------------------------------------------- |
| `backend.grpc.keepalive.timeMs` | The number of ms between each client keepalive ping | `120000` |
| `backend.kaniko.cache.warmer.image` | The docker image for the kaniko cache warmer | `gcr.io/kaniko-project/warmer:v1.0.0` |
| `backend.kaniko.cache.warmer.images` | A list of docker images to warm up the kaniko local cache with | `[]` |
| `backend.kaniko.cache.warmer.images[].image` | A docker image | (undefined) |
| `backend.kaniko.image` | The docker image for kaniko builds | `gcr.io/kaniko-project/executor:v1.0.0` |
| `backend.kaniko.mirror` | If true, pull base images from the local registry | `False` |
| `channels` | A list of Hyperledger Fabric channels to connect to. See [hlf-k8s](https://github.com/SubstraFoundation/hlf-k8s). | `[mychannel]` |
| `events.nodeSelector` | Node labels for pod assignment | `{}` |
| `events.tolerations` | Toleration labels for pod assignment | `[]` |
| `events.affinity` | Affinity settings for pod assignment | `{}` |
| `httpClient.timeoutSeconds` | The timeout in seconds for outgoing HTTP requests  | `30` |
| `registry.prepopulate` | A list of docker images to prepopulate the local docker registry with | `[]` |
| `registry.prepopulate[].image` | A docker image | (undefined) |
| `registry.prepopulate[].sourceRegistry` | The URL of a docker registry to pull the image from (leave blank for Docker Hub) | (undefined) |
| `registry.prepopulate[].dockerConfigSecretName` | Optionally, a docker config to use when pulling the docker image | (undefined) |
| `users` | A list of users who can log into the backend | `[]` |
| `users[].name` | The user login | (undefined) |
| `users[].password` | The user password | (undefined) |
| `users[].channel` | The user channel. This is the name of a Hyperledger Fabric channel (see [hlf-k8s](https://github.com/SubstraFoundation/hlf-k8s)). All operations by the user will be executed against this channel. | (undefined) |


## Usage

### Basic example

For a simple example, see the [skaffold.yaml](../../skaffold.yaml) file.

