# Substra Backend

Substra Backend is a component of [Substra](https://github.com/SubstraFoundation/substra).

## Prerequisites

- Kubernetes 1.19+
- If you want to enable GPU support, install the nvidia device plugin for kubernetes: https://github.com/NVIDIA/k8s-device-plugin or https://github.com/NVIDIA/gpu-operator

## Changelog

See [CHANGELOG.md](./CHANGELOG.md)

## Parameters

### Global Substra settings

| Name                             | Description                                                                                                                                                                        | Value                |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| `settings`                       | The settings to use for substra (`prod` or `dev`)                                                                                                                                  | `prod`               |
| `config`                         | The configuration to use for substra                                                                                                                                               | `{}`                 |
| `organizationName`               | Current organization name                                                                                                                                                          | `owkin`              |
| `DataSampleStorageInServerMedia` | If set to true, Datasamples which are registered by a "path" are kept on the "servermedias" volume. If set to `false` (default value), the datasample will be duplicated to MinIO. | `false`              |
| `privateCa.enabled`              | Run the init container injecting the private CA certificate                                                                                                                        | `false`              |
| `privateCa.image.repository`     | Private CA injector image                                                                                                                                                          | `ubuntu`             |
| `privateCa.image.tag`            | Private CA injector tag                                                                                                                                                            | `latest`             |
| `privateCa.image.pullPolicy`     | Private CA injector pull policy                                                                                                                                                    | `IfNotPresent`       |
| `privateCa.image.apkAdd`         | Install the update-ca-certificates package                                                                                                                                         | `true`               |
| `privateCa.configMap.name`       | Name of the _ConfigMap_ containing the private CA certificate                                                                                                                      | `substra-private-ca` |
| `privateCa.configMap.data`       | Certificate to add in the _ConfigMap_                                                                                                                                              | `nil`                |
| `privateCa.configMap.fileName`   | Certificate filename in the _ConfigMap_                                                                                                                                            | `private-ca.crt`     |
| `psp.create`                     | Create a _Pod Security Policy_ in the cluster. WARNING: PodSecurityPolicy is deprecated in Kubernetes 1.21 or later and unavailable in Kubernetes 1.25 or later                    | `true`               |


### Server settings

| Name                                        | Description                                                                                                                                        | Value                            |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| `server.replicaCount`                       | Number of server replicas                                                                                                                          | `1`                              |
| `server.defaultDomain`                      | The hostname and port of the backend. This address will be used as the assets `storage_address` field                                              | `localhost`                      |
| `server.subpath`                            | The subpath under which the API is served                                                                                                          | `""`                             |
| `server.commonHostDomain`                   | The common host under which the backend and frontend are served                                                                                    | `""`                             |
| `server.uwsgiProcesses`                     | The number of uwsgi processes                                                                                                                      | `20`                             |
| `server.uwsgiThreads`                       | The number of uwsgi threads                                                                                                                        | `10`                             |
| `server.image.registry`                     | Substra backend server image registry                                                                                                              | `gcr.io`                         |
| `server.image.repository`                   | Substra backend server image repository                                                                                                            | `connect-314908/connect-backend` |
| `server.image.tag`                          | Substra backend server image tag                                                                                                                   | `0.4.0`                          |
| `server.image.pullPolicy`                   | Substra backend server image pull policy                                                                                                           | `IfNotPresent`                   |
| `server.image.pullSecrets`                  | Specify image pull secrets                                                                                                                         | `[]`                             |
| `server.podSecurityContext.enabled`         | Enable security context                                                                                                                            | `true`                           |
| `server.podSecurityContext.runAsUser`       | User ID for the pod                                                                                                                                | `1001`                           |
| `server.podSecurityContext.runAsGroup`      | Group ID for the pod                                                                                                                               | `1001`                           |
| `server.podSecurityContext.fsGroup`         | FileSystem group ID for the pod                                                                                                                    | `1001`                           |
| `server.service.type`                       | Kubernetes Service type                                                                                                                            | `ClusterIP`                      |
| `server.service.port`                       | Server port                                                                                                                                        | `8000`                           |
| `server.service.clusterIP`                  | _ClusterIP_ or `None` for headless service                                                                                                         | `""`                             |
| `server.service.loadBalancerIP`             | Load balancer IP if service type is `LoadBalancer`                                                                                                 | `""`                             |
| `server.service.loadBalancerSourceRanges`   | Addresses that are allowed when service is `LoadBalancer`                                                                                          | `[]`                             |
| `server.service.nodePort`                   | Specify the `nodePort` value for the `LoadBalancer` and `NodePort` service types                                                                   | `""`                             |
| `server.service.externalIPs`                | A list of IP addresses for which nodes in the cluster will also accept traffic for this service                                                    | `[]`                             |
| `server.service.annotations`                | Additional annotations for the _Service_ resource.                                                                                                 | `{}`                             |
| `server.ingress.enabled`                    | Deploy an ingress for the substra backend server                                                                                                   | `false`                          |
| `server.ingress.hostname`                   | Default host for the ingress ressource                                                                                                             | `substra.backend.local`          |
| `server.ingress.pathType`                   | Ingress path type                                                                                                                                  | `ImplementationSpecific`         |
| `server.ingress.path`                       | Path for the default host                                                                                                                          | `/`                              |
| `server.ingress.extraPaths`                 | The list of extra paths to be created for the default host                                                                                         | `[]`                             |
| `server.ingress.annotations`                | Additional annotations for the Ingress resource.                                                                                                   | `{}`                             |
| `server.ingress.extraHosts`                 | The list of additional hostnames to be covered with this ingress record                                                                            | `[]`                             |
| `server.ingress.extraTls`                   | The tls configuration for hostnames to be coverred by the ingress                                                                                  | `[]`                             |
| `server.ingress.ingressClassName`           | _IngressClass_ that will be used to implement the Ingress                                                                                          | `nil`                            |
| `server.resources`                          | Server container resources requests and limits                                                                                                     | `{}`                             |
| `server.persistence.storageClass`           | Specify the _StorageClass_ used to provision the volume. Or the default _StorageClass_ will be used. Set it to `-` to disable dynamic provisioning | `""`                             |
| `server.persistence.servermedias.size`      | Servermedias volume size                                                                                                                           | `10Gi`                           |
| `server.livenessProbe.enabled`              | Enable livenessProbe                                                                                                                               | `true`                           |
| `server.livenessProbe.path`                 | Path of the HTTP service for checking the healthy state                                                                                            | `/liveness`                      |
| `server.livenessProbe.initialDelaySeconds`  | Initial delay seconds for livenessProbe                                                                                                            | `60`                             |
| `server.livenessProbe.periodSeconds`        | Period seconds for livenessProbe                                                                                                                   | `45`                             |
| `server.livenessProbe.timeoutSeconds`       | Timeout seconds for livenessProbe                                                                                                                  | `5`                              |
| `server.livenessProbe.failureThreshold`     | Failure threshold for livenessProbe                                                                                                                | `6`                              |
| `server.livenessProbe.successThreshold`     | Success threshold for livenessProbe                                                                                                                | `1`                              |
| `server.readinessProbe.enabled`             | Enable readinessProbe                                                                                                                              | `true`                           |
| `server.readinessProbe.path`                | Path of the HTTP service for checking the healthy state                                                                                            | `/readiness`                     |
| `server.readinessProbe.initialDelaySeconds` | Initial delay seconds for readinessProbe                                                                                                           | `5`                              |
| `server.readinessProbe.periodSeconds`       | Period seconds for readinessProbe                                                                                                                  | `30`                             |
| `server.readinessProbe.timeoutSeconds`      | Timeout seconds for readinessProbe                                                                                                                 | `2`                              |
| `server.readinessProbe.failureThreshold`    | Failure threshold for readinessProbe                                                                                                               | `3`                              |
| `server.readinessProbe.successThreshold`    | Success threshold for readinessProbe                                                                                                               | `1`                              |


### Substra worker settings

| Name                                           | Description                                                                                                                                        | Value                            |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| `worker.replicaCount`                          | Replica count for the worker service                                                                                                               | `1`                              |
| `worker.concurrency`                           | Maximum amount of tasks to process in parallel                                                                                                     | `1`                              |
| `worker.image.registry`                        | Substra backend worker image registry                                                                                                              | `gcr.io`                         |
| `worker.image.repository`                      | Substra backend worker image repository                                                                                                            | `connect-314908/connect-backend` |
| `worker.image.tag`                             | Substra backend worker image tag                                                                                                                   | `0.4.0`                          |
| `worker.image.pullPolicy`                      | Substra backend worker image pull policy                                                                                                           | `IfNotPresent`                   |
| `worker.image.pullSecrets`                     | Specify image pull secrets                                                                                                                         | `[]`                             |
| `worker.podSecurityContext.enabled`            | Enable security context                                                                                                                            | `true`                           |
| `worker.podSecurityContext.runAsUser`          | User ID for the pod                                                                                                                                | `1001`                           |
| `worker.podSecurityContext.runAsGroup`         | Group ID for the pod                                                                                                                               | `1001`                           |
| `worker.podSecurityContext.fsGroup`            | FileSystem group ID for the pod                                                                                                                    | `1001`                           |
| `worker.resources`                             | Worker container resources requests and limits                                                                                                     | `{}`                             |
| `worker.nodeSelector`                          | Node labels for pod assignment                                                                                                                     | `{}`                             |
| `worker.tolerations`                           | Toleration labels for pod assignment                                                                                                               | `[]`                             |
| `worker.affinity`                              | Affinity settings for pod assignment, ignored if `DataSampleStorageInServerMedia` is `true`                                                        | `{}`                             |
| `worker.rbac.create`                           | Create a role and service account for the worker                                                                                                   | `true`                           |
| `worker.persistence.storageClass`              | Specify the _StorageClass_ used to provision the volume. Or the default _StorageClass_ will be used. Set it to `-` to disable dynamic provisioning | `""`                             |
| `worker.persistence.size`                      | The size of the volume. The size of this volume should be sufficient to store many assets.                                                         | `10Gi`                           |
| `worker.computePod.maxStartupWaitSeconds`      | Set the maximum amount of time we will wait for the compute pod to be ready                                                                        | `300`                            |
| `worker.computePod.securityContext.fsGroup`    | Set the filesystem group for the Compute pod                                                                                                       | `1001`                           |
| `worker.computePod.securityContext.runAsUser`  | Set the user for the Compute pod                                                                                                                   | `1001`                           |
| `worker.computePod.securityContext.runAsGroup` | Set the group for the Compute pod                                                                                                                  | `1001`                           |


### Substra periodic tasks worker settings

| Name                                            | Description                                       | Value                            |
| ----------------------------------------------- | ------------------------------------------------- | -------------------------------- |
| `schedulerWorker.replicaCount`                  | Replica count for the periodic tasks worker       | `1`                              |
| `schedulerWorker.image.registry`                | Substra backend tasks scheduler image registry    | `gcr.io`                         |
| `schedulerWorker.image.repository`              | Substra backend tasks scheduler image repository  | `connect-314908/connect-backend` |
| `schedulerWorker.image.tag`                     | Substra backend tasks scheduler image tag         | `0.4.0`                          |
| `schedulerWorker.image.pullPolicy`              | Substra backend task scheduler image pull policy  | `IfNotPresent`                   |
| `schedulerWorker.image.pullSecrets`             | Specify image pull secrets                        | `[]`                             |
| `schedulerWorker.nodeSelector`                  | Node labels for pod assignment                    | `{}`                             |
| `schedulerWorker.tolerations`                   | Toleration labels for pod assignment              | `[]`                             |
| `schedulerWorker.affinity`                      | Affinity settings for pod assignment              | `{}`                             |
| `schedulerWorker.resources`                     | Scheduler container resources requests and limits | `{}`                             |
| `schedulerWorker.podSecurityContext.enabled`    | Enable security context                           | `true`                           |
| `schedulerWorker.podSecurityContext.runAsUser`  | User ID for the pod                               | `1001`                           |
| `schedulerWorker.podSecurityContext.runAsGroup` | Group ID for the pod                              | `1001`                           |
| `schedulerWorker.podSecurityContext.fsGroup`    | FileSystem group ID for the pod                   | `1001`                           |


### Celery task scheduler settings

| Name                                      | Description                                       | Value                            |
| ----------------------------------------- | ------------------------------------------------- | -------------------------------- |
| `scheduler.replicaCount`                  | Replica count for the scheduler server            | `1`                              |
| `scheduler.image.registry`                | Subsra backend tasks scheduler image registry     | `gcr.io`                         |
| `scheduler.image.repository`              | Substra backend tasks scheduler image repository  | `connect-314908/connect-backend` |
| `scheduler.image.tag`                     | Substra backend tasks scheduler image tag         | `0.4.0`                          |
| `scheduler.image.pullPolicy`              | Substra backend task scheduler image pull policy  | `IfNotPresent`                   |
| `scheduler.image.pullSecrets`             | Specify image pull secrets                        | `[]`                             |
| `scheduler.resources`                     | Scheduler container resources requests and limits | `{}`                             |
| `scheduler.nodeSelector`                  | Node labels for pod assignment                    | `{}`                             |
| `scheduler.tolerations`                   | Toleration labels for pod assignment              | `[]`                             |
| `scheduler.affinity`                      | Affinity settings for pod assignment              | `{}`                             |
| `scheduler.podSecurityContext.enabled`    | Enable security context                           | `true`                           |
| `scheduler.podSecurityContext.runAsUser`  | User ID for the pod                               | `1001`                           |
| `scheduler.podSecurityContext.runAsGroup` | Group ID for the pod                              | `1001`                           |
| `scheduler.podSecurityContext.fsGroup`    | FileSystem group ID for the pod                   | `1001`                           |


### Substra container registry settings

| Name                            | Description                                                                                     | Value       |
| ------------------------------- | ----------------------------------------------------------------------------------------------- | ----------- |
| `containerRegistry.local`       | Whether the registry is exposed as a _nodePort_ and located in the same _Namespace_ as Substra. | `true`      |
| `containerRegistry.host`        | Hostname of the container registry                                                              | `127.0.0.1` |
| `containerRegistry.port`        | Port of the container registry                                                                  | `32000`     |
| `containerRegistry.scheme`      | Communication scheme of the container registry                                                  | `http`      |
| `containerRegistry.pullDomain`  | Hostname from which the cluster should pull container images                                    | `127.0.0.1` |
| `containerRegistry.prepopulate` | Images to add to the container registry                                                         | `[]`        |


### Event app settings

| Name                                   | Description                                         | Value                            |
| -------------------------------------- | --------------------------------------------------- | -------------------------------- |
| `events.image.registry`                | Substra event app image registry                    | `gcr.io`                         |
| `events.image.repository`              | Substra event app image repository                  | `connect-314908/connect-backend` |
| `events.image.tag`                     | Substra event app image tag                         | `0.4.0`                          |
| `events.image.pullPolicy`              | Substra event app image pull policy                 | `IfNotPresent`                   |
| `events.image.pullSecrets`             | Specify image pull secrets                          | `[]`                             |
| `events.podSecurityContext.enabled`    | Enable security context                             | `true`                           |
| `events.podSecurityContext.runAsUser`  | User ID for the pod                                 | `1001`                           |
| `events.podSecurityContext.runAsGroup` | Group ID for the pod                                | `1001`                           |
| `events.podSecurityContext.fsGroup`    | FileSystem group ID for the pod                     | `1001`                           |
| `events.nodeSelector`                  | Node labels for pod assignment                      | `{}`                             |
| `events.tolerations`                   | Toleration labels for pod assignment                | `[]`                             |
| `events.affinity`                      | Affinity settings for pod assignment                | `{}`                             |
| `events.rbac.create`                   | Create a role and service account for the event app | `true`                           |
| `events.serviceAccount.create`         | Create a service account for the event app          | `true`                           |
| `events.serviceAccount.name`           | The name of the ServiceAccount to use               | `""`                             |


### Orchestrator settings

| Name                                                      | Description                                                                                                            | Value                       |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| `orchestrator.host`                                       | The orchestrator gRPC endpoint                                                                                         | `orchestrator.local`        |
| `orchestrator.port`                                       | The orchestrator gRPC port                                                                                             | `9000`                      |
| `orchestrator.tls.enabled`                                | Enable TLS for the gRPC endpoint                                                                                       | `false`                     |
| `orchestrator.tls.cacert`                                 | A configmap containing the orchestrator CA certificate. Use this if your orchestrator uses a private CA.               | `nil`                       |
| `orchestrator.tls.mtls.enabled`                           | Enable client verification for the orchestrator gRPC endpoint                                                          | `false`                     |
| `orchestrator.tls.mtls.clientCertificate`                 | A secret containing the client certificate `tls.crt` and private key `tls.key`                                         | `nil`                       |
| `orchestrator.rabbitmq.host`                              | The orchestrator RabbitMQ endpoint hostname                                                                            | `events.orchestrator.local` |
| `orchestrator.rabbitmq.port`                              | The orchestrator RabbitMQ port                                                                                         | `5672`                      |
| `orchestrator.rabbitmq.auth.username`                     | The orchestrator RabbitMQ username                                                                                     | `user`                      |
| `orchestrator.rabbitmq.auth.password`                     | The orchestrator RabbitMQ password                                                                                     | `password`                  |
| `orchestrator.rabbitmq.tls.enabled`                       | Enable TLS for the orchestrator RabbitMQ endpoint                                                                      | `false`                     |
| `orchestrator.rabbitmq.tls.clientCertificate`             | A secret containing the client certificate `tls.crt` and private key `tls.key`                                         | `nil`                       |
| `orchestrator.mspID`                                      | current node name on the Orchestrator                                                                                  | `OwkinPeerMSP`              |
| `orchestrator.channels[0].mychannel.restricted`           | Make this channel restricted to a single node. The server will fail if there is more than one instance in this channel | `false`                     |
| `orchestrator.channels[0].mychannel.model_export_enabled` | Allow logged-in users to download models trained on this node                                                          | `false`                     |
| `orchestrator.channels[0].mychannel.chaincode.name`       | The name of the chaincode instantiated on this channel                                                                 | `mycc`                      |


### Kaniko settings

| Name                                    | Description                                                                                                                                        | Value                     |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `kaniko.image.registry`                 | Kaniko image registry                                                                                                                              | `gcr.io`                  |
| `kaniko.image.repository`               | Kaniko image repository                                                                                                                            | `kaniko-project/executor` |
| `kaniko.image.tag`                      | Kaniko image tag                                                                                                                                   | `v1.6.0`                  |
| `kaniko.mirror`                         | If set to `true` pull base images from the local registry.                                                                                         | `false`                   |
| `kaniko.dockerConfigSecretName`         | A Docker config to use for pulling base images                                                                                                     | `nil`                     |
| `kaniko.cache.warmer.image.registry`    | Kaniko cache warmer registry                                                                                                                       | `gcr.io`                  |
| `kaniko.cache.warmer.image.repository`  | Kaniko cache warmer repository                                                                                                                     | `kaniko-project/warmer`   |
| `kaniko.cache.warmer.image.tag`         | Kaniko cache warmer image tag                                                                                                                      | `v1.6.0`                  |
| `kaniko.cache.warmer.cachedImages`      | A list of docker images to warmup the Kaniko cache                                                                                                 | `[]`                      |
| `kaniko.cache.persistence.storageClass` | Specify the _StorageClass_ used to provision the volume. Or the default _StorageClass_ will be used. Set it to `-` to disable dynamic provisioning | `""`                      |
| `kaniko.cache.persistence.size`         | The size of the volume.                                                                                                                            | `10Gi`                    |


### Account operator settings

| Name                               | Description                                                                | Value |
| ---------------------------------- | -------------------------------------------------------------------------- | ----- |
| `addAccountOperator.resources`     | add-account-operator resources requests and limits                         | `{}`  |
| `addAccountOperator.outgoingNodes` | Outgoind nodes credentials for substra backend node-to-node communications | `[]`  |
| `addAccountOperator.incomingNodes` | Incoming nodes credentials for substra backend node-to-node communications | `[]`  |
| `addAccountOperator.users`         | A list of users who can log into the substra backend server                | `[]`  |


### Helm hooks

| Name                                       | Description                                                                 | Value             |
| ------------------------------------------ | --------------------------------------------------------------------------- | ----------------- |
| `hooks.serviceAccount`                     | Service account to use for the helm hooks                                   | `""`              |
| `hooks.deleteWorkerPvc.enabled`            | Enable the deletion of deployed compute pods after the application deletion | `false`           |
| `hooks.deleteWorkerPvc.image.repository`   | Image repository for the hook image                                         | `bitnami/kubectl` |
| `hooks.deleteWorkerPvc.image.tag`          | Image tag for the hook image                                                | `latest`          |
| `hooks.deleteComputePods.enabled`          | Enable the deletion of the worker PVCs after the application deletion       | `false`           |
| `hooks.deleteComputePods.image.repository` | Image repository for the hook image                                         | `bitnami/kubectl` |
| `hooks.deleteComputePods.image.tag`        | Image tag for the hook image                                                | `latest`          |


## Usage

### Basic example

For a simple example, see the [skaffold.yaml](../../skaffold.yaml) file.

### Kaniko builder and private registry

To be able to build images based on a private registry you need to provide `backend.kaniko.dockerConfigSecretName`

For instance, for GCR, it can be done like this

```
gcloud auth login
gcloud iam service-accounts keys create /tmp/sa-key.json --iam-account=sa-name@project-id.iam.gserviceaccount.com

kubectl create secret docker-registry docker-config --docker-server=gcr.io --docker-username=_json_key --docker-password="$(cat /tmp/sa-key.json)" -n org-1
kubectl create secret docker-registry docker-config --docker-server=gcr.io --docker-username=_json_key --docker-password="$(cat /tmp/sa-key.json)" -n org-2

```

Where `docker-config` is the name of the docker config secret which needs to be used.

### Data sample storage {#datasample-storage}

By default (`DataSampleStorageInServerMedia` set to `False`), all the datasamples are stored in MinIO.

_In a context where there is only one kubernetes node only_: it is possible to set `DataSampleStorageInServerMedia` to `true`. In this case, the datasamples that are registered by a "path" are kept on the "servermedias" volume. If set to `false` (default value), the datasample will be duplicated to MinIO.

Activating this option prevents the datasamples from being duplicated in the servermedia and MinIO.

It is recommended to activate this option for environments that have limited storage available.

Note that if `DataSampleStorageInServerMedia` is set to `true`, scaling is not supported: it will not be possible to increase the number of kubernetes nodes, nor of workers without re-registering all the datasamples. This even if `DataSampleStorageInServerMedia` is set back to `false`.

Also note that registering datasamples by sending a file will work in the same way independently from this option: in either cases the file will be uploaded to MinIO.

For additional information: [here](https://github.com/Substra/substra/blob/master/references/sdk.md#add_data_sample) is the documentation of Substra SDK for registering datasamples.


You will also have to create manually a PersistentVolume for each organization

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-local-servermedias
  labels:
    app.kubernetes.io/instance: backend-{{ Release.Name }}
spec:
  storageClassName: manual
  capacity:
    storage: 20Gi ## Should be equal or bigger than .Values.server.persistence.servermedias.size
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/PATH/TO/YOUR/LOCAL_STORAGE"


```
