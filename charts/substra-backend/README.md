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
| `channels` | A list of Hyperledger Fabric channels to connect to. See [hlf-k8s](https://github.com/SubstraFoundation/hlf-k8s). | `[mychannel]` |
| `users` | A list of users who can log into the backend | `[]` |
| `users[].name` | The user login | (undefined) |
| `users[].password` | The user password | (undefined) |
| `users[].channel` | The user channel. This is the name of a Hyperledger Fabric channel (see [hlf-k8s](https://github.com/SubstraFoundation/hlf-k8s)). All operations by the user will be executed against this channel. | (undefined) |


## Usage

### Basic example

For a simple example, see the [skaffold.yaml](../../skaffold.yaml) file.

