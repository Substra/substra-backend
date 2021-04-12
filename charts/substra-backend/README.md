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
| `backend.replicaCount` | Replica count for substra-backend server service | `1` |
| `backend.settings` | The settings to use to deploy substra-backend, can be `prod` or `dev`| `prod` |
| `backend.tokenStrategy` | Token strategy to use. If `unique`, a user may only have one active session at a time. With `reuse`, a user may open multiple concurrent sessions | `unique` |
| `backend.defaultDomain` | The hostname and port corresponding to the backend. This domain will be referenced in the "storage_address" of the ledger assets. | `localhost` |
| `backend.uwsgiProcesses` | Number of uswgi processes | `20` |
| `backend.uwsgiThreads` | Number of uwsgi threads per process | `2` |
| `backend.gzipModels` | Enable models compression before transmission | `False` |
| `backend.kaniko.cache.warmer.image` | The docker image for the kaniko cache warmer | `gcr.io/kaniko-project/warmer:v1.0.0` |
| `backend.kaniko.cache.warmer.images` | A list of docker images to warm up the kaniko local cache with | `[]` |
| `backend.kaniko.cache.warmer.images[].image` | A docker image | (undefined) |
| `backend.kaniko.image` | The docker image for kaniko builds | `gcr.io/kaniko-project/executor:v1.3.0` |
| `backend.kaniko.mirror` | If true, pull base images from the local registry | `False` |
| `backend.compute.registry` | Optionally, the URL of a registry to pull the kaniko image from (`backend.kaniko.image`). This image will be used to build client images (compute tasks) | `nil` |
| `backend.image.repository` | `substra-backend` image repository | `substrafoundation/substra-backend` |
| `backend.image.tag` | `substra-backend` image tag | `latest` |
| `backend.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `backend.image.pullSecrets` | Image pull secrets | `[]` |
| `backend.service.type` | Kubernetes Service type | `NodePort` |
| `backend.service.port` | substra-backend service port | `8000` |
| `backend.service.loadBalancerSourceRanges` | CIDR range of IP addresses allowed to access the service, when the service is of type LoadBalancer | `[]` |
| `backend.service.loadBalancerIP`  | LoadBalancerIP for the service | `nil` |
| `backend.service.clusterIP` | ClusterIP for the service | `nil` |
| `backend.service.externalIP` | ExternalIP for the service | `[]` |
| `backend.service.labels` | Service labels | `{}` (evaluated as a template) |
| `backend.service.annotations` | Service annotations | `{}` (evaluated as a template) |
| `backend.ingress.enabled` | Enable ingress resource for Management console | `False` |
| `backend.ingress.annotations` | Ingress annotations | `{}`                           |
| `backend.ingress.hosts[].host` | Hostname for the ingress resource | `chart-example.local`
| `backend.ingress.hosts[].paths` | Paths for the host | `[]` |
| `backend.ingress.tls` | TLS configuration for the hosts defined in `backend.ingress.hosts[]`| `[]` |
| `backend.resources` | Resources configuration for the `substra-backend` container | `{}` |
| `backend.grpc.keepalive.timeMs` | The number of milliseconds between each client GRPC keepalive ping | `120000` |
| `outgoingNodes[]` | Outgoing nodes credentials for substra-backend node-to-node communication | `[]` |
| `outgoingNodes[].name` | Outgoing node username | (undefined) |
| `outgoingNodes[].secret` | Outgoing node password | (undefined) |
| `incomingNodes[]` | Incoming nodes credentials for substra-backend node-to-node communication | `[]` |
| `incomingNodes[].name` | Incoming node username | `[]` |
| `incomingNodes[].secret` | Incoming nodes password | (undefined) |
| `users` | A list of users who can log into the backend | (undefined) |
| `users[].name` | The user login | (undefined) |
| `users[].password` | The user password | (undefined) |
| `users[].channel` | The user channel. This is the name of a Hyperledger Fabric channel (see [hlf-k8s](https://github.com/SubstraFoundation/hlf-k8s)). All operations by the user will be executed against this channel. | (undefined) |
| `persistence.storageClassName` | PVC Storage Class name for data volumes | (undefined) |
| `persistence.hostPath` | Host path for PVC Storage in case of local storage | (undefined) |
| `persistence.hostPathServerMedias` | Server medias host path for server medias PVC Storage in case of local storage | (undefined) |
| `persistence.size` |  PVC Storage Request for data volume | `10Gi` |
| `persistence.volumes` | Additional volumes definition for substra-backend assets storage | `algos, ..., local` |
| `persistence.volumes[].size` | Additional volume size | |
| `persistence.volumes[].readOnly.server` | If true, the additional volume will be read-only on the backend-server pod | |
| `persistence.volumes[].readOnly.worker` | If true, the additional volume will be read-only on the backend-worker pod | |
| `secrets.caCert` | Hyperledger Fabric Peer CA Cert  | `hlf-cacert` |
| `secrets.user.cert` | Hyperledger Fabric Peer user certificate | `hlf-msp-cert-user` |
| `secrets.user.key` | Hyperledger Fabric Peer user key | `hlf-msp-key-user` |
| `secrets.peer.tls.client` | Hyperledger Fabric Peer TLS client key/cert | `hlf-tls-user` |
| `secrets.peer.tls.server` | Hyperledger Fabric Peer TLS server key/cert | `hlf-tls-admin` |
| `user.name` | Hyperledger Fabric Peer user name | `user` |
| `organization.name` | Hyperledger Fabric Peer organization name | `substra` |
| `peer.host` | The Hyperledger Fabric peer hostname | `healthchain-peer.owkin.com` |
| `peer.port` | The Hyperledger Fabric peer port | `443` |
| `peer.mspID` | The Hyperledger Fabric peer MSP ID | `OwkinPeerMSP` |
| `peer.waitForEventTimeoutSeconds` | Time to wait for confirmation from the peers that the transaction has been committed successfully | `45` |
| `peer.strategy.invoke` | Chaincode invocation endorsement strategy. Can be `SELF` or `ALL` (request endorsement from all peers) | `ALL` |
| `peer.strategy.query` | Chaincode query endorsement strategy. Can be `SELF` or `ALL` (request endorsement from all peers) | `SELF` |
| `channels` | A list of Hyperledger Fabric channels to connect to. See [hlf-k8s](https://github.com/SubstraFoundation/hlf-k8s). | `{ mychannel: { restricted: False, chaincode: { name: mycc, version: 1.0 } } }` |
| `channels[].restricted` | If true, the channel must have at most 1 member, else the backend readiness/liveliness probes will fail. | (undefined) |
| `channels[].chaincode.name` | The name of the chaincode instantiated on this channel. | (undefined) |
| `channels[].chaincode.version` | The version of the chaincode instantiated on this channel. | (undefined) |
| `postgresql` | PostgreSQL configuration. For more info, See [postgresql](https://github.com/bitnami/charts/tree/master/bitnami/postgresql) | |
| `postgresql.enabled` | If true, enable PostgreSQL database | `true` |
| `postgresql.postgresqlDatabase` | PostgreSQL database | `substra` |
| `postgresql.postgresqlUsername` | PostgreSQL username | `postgres` |
| `postgresql.postgresqlPassword` | PostgreSQL admin password  | `postgres` |
| `postgresql.persistence.enabled` | Enable PostgreSQL persistence using PVC | `false` |
| `rabbitmq` | RabbitMQ configuration. For more info, see [rabbitmq](https://github.com/bitnami/charts/tree/master/bitnami/rabbitmq) | |
| `rabbitmq.enabled` | Enable RabbitMQ database | `true` |
| `rabbitmq.rabbitmq.username` | RabbitMQ username | `rabbitmq` |
| `rabbitmq.rabbitmq.password` | RabbitMQ admin password  | `rabbitmq` |
| `rabbitmq.host` | RabbitMQ hostname | `rabbitmq` |
| `rabbitmq.port` | RabbitMQ port | `5672` |
| `rabbitmq.persistence.enabled` | Enable RabbitMQ persistence using PVC | `false` |
| `docker-registry` | Docker Registry configuration. For more info, See [docker-registry](https://artifacthub.io/packages/helm/twuni/docker-registry) | |
| `docker-registry.enabled` | If true, enable the local docker registry | `true` |
| `docker-registry.storage` | Storage system to use | `filesystem` |
| `docker-registry.persistence.enabled` | Enable Docker Registry persistence using PVC | `true` |
| `docker-registry.persistence.size` | Amount of space to claim for PVC | `10Gi` |
| `docker-registry.persistence.deleteEnabled` | Enable the deletion of image blobs and manifests by digest | `true` |
| `docker-registry.service.type` | service type (If you use the local docker registry, you must use a `NodePort` to expose it kubernetes) | `NodePort` |
| `docker-registry.service.nodePort` | if `docker-registry.service.type` is `NodePort` and this is non-empty, sets the node port of the service | (undefined) |
| `docker-registry.images.duration` | Maximum image duration before removal in seconds| `604800` |
| `celerybeat.replicaCount` | Replica count for celerybeat service | `1` |
| `celerybeat.expiredTokensFlushPeriod` | Flushing of expired tokens task period | `86400` |
| `celerybeat.taskPeriod` | Celery beat task period | `10800` |
| `celerybeat.image.repository` | `celerybeat` image repository | `substrafoundation/substra-backend` |
| `celerybeat.image.tag` | `celerybeat` image tag | `latest` |
| `celerybeat.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `celerybeat.image.pullSecrets` | Image pull secrets | `[]` |
| `celerybeat.resources` | Resources configuration for the `celerybeat` container | `{}` |
| `celerybeat.nodeSelector` | Node labels for pod assignment | `{}` |
| `celerybeat.tolerations` | Toleration labels for pod assignment | `[]` |
| `celerybeat.affinity` | Affinity settings for pod assignment | `{}` |
| `celeryscheduler.resources` | Resources configuration for the `celeryscheduler` container | `{}` |
| `celeryworker.replicaCount` | Replica count for celeryworker service | `1` |
| `celeryworker.concurrency` | Celery worker concurrency  (max task to process in parallel) | `1` |
| `celeryworker.updateStrategy` | Pod update strategy| `RollingUpdate` |
| `celeryworker.image.repository` | `celeryworker` image repository | `substrafoundation/substra-backend` |
| `celeryworker.image.tag` | `celeryworker` image tag | `latest` |
| `celeryworker.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `celeryworker.image.pullSecrets` | Image pull secrets | `[]` |
| `celeryworker.resources` | Resources configuration for the `celeryworker` container | `{}` |
| `celeryworker.nodeSelector` | Node labels for pod assignment | `{}` |
| `celeryworker.tolerations` | Toleration labels for pod assignment | `[]` |
| `celeryworker.affinity` | Affinity settings for pod assignment | `{}` |
| `celeryworker.rbac.enable` | Enable rbac for the celery worker | `True` |
| `events.nodeSelector` | Node labels for pod assignment | `{}` |
| `events.tolerations` | Toleration labels for pod assignment | `[]` |
| `events.affinity` | Affinity settings for pod assignment | `{}` |
| `extraEnv[]` | Additional environment variables to add to substra-backend pods | `[]` |
| `extraEnv[].name` | Environment variable name | (undefined) |
| `extraEnv[].value` | Environment variable value | (undefined) |
| `privateCa.enabled` | if true, use a private CA | `False` |
| `privateCa.image.repository` | Image for the private CA | `alpine:latest` |
| `privateCa.image.pullPolicy` | Image pull policy for the private CA | `IfNotPresent` |
| `privateCa.image.apkAdd` | if true, enable apk add | `true` |
| `privateCa.configMap.name` | The name of the ConfigMap containing the private CA certificate | `substra-private-ca` |
| `privateCa.configMap.fileName` | The CA certificate filename within the ConfigMap | `private-ca.crt` |
| `httpClient.timeoutSeconds` | The timeout in seconds for outgoing HTTP requests  | `30` |
| `registry.local` | If you use an external docker-registry, must be set to false (host and port will be taken into account). See also: `docker-registry.enabled` | `true` |
| `registry.host` | Hostname of the external docker-registry, if `local` is false | `127.0.0.1` |
| `registry.port` | Port of the external docker-registry, if `local` is false | `32000` |
| `registry.scheme` | Scheme to use to pull image | `http` |
| `registry.pullDomain` | The domain to pull docker images from. If `registry.local` is false, set this value to your docker registry `<host>:<port>`. If `registry.local` is true, then set this value to  `127.0.0.1`. If `registry.local` is true and `docker-registry.service.nodePort` is set to an arbitrary port number, then set to `127.0.0.1:<nodePort>` | `127.0.0.1` |
| `registry.prepopulate[]` | A list of docker images to prepopulate the local docker registry with | `[]` |
| `registry.prepopulate[].image` | A docker image | (undefined) |
| `registry.prepopulate[].sourceRegistry` | The URL of a docker registry to pull the image from (leave blank for Docker Hub) | (undefined) |
| `registry.prepopulate[].dockerConfigSecretName` | Optionally, a docker config to use when pulling the docker image | (undefined) |
| `psp.create` | If true, create a Pod Security Policy | `True` |
| `securityContext.enabled` | If true, enable Pod Security Context | `True` |
| `securityContext.fsGroup` | Pod Security Context filesystem group ID | `1001` |
| `securityContext.runAsUser` | Pod Security Context user ID | `1001` |
| `securityContext.runAsGroup` | Pod Security Context group ID | `1001` |

## Usage

### Basic example

For a simple example, see the [skaffold.yaml](../../skaffold.yaml) file.
