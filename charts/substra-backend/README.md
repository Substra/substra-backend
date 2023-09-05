# Substra Backend

Substra Backend is a component of [Substra](https://github.com/SubstraFoundation/substra).

## Prerequisites

- Kubernetes 1.19+
- If you want to enable GPU support, install the nvidia device plugin for kubernetes: https://github.com/NVIDIA/k8s-device-plugin or https://github.com/NVIDIA/gpu-operator

## Changelog

See [CHANGELOG.md](https://github.com/Substra/substra-backend/blob/main/charts/substra-backend/CHANGELOG.md)

## Upgrade

See [UPGRADE.md](https://github.com/Substra/substra-backend/blob/main/charts/substra-backend/UPGRADE.md)

## Parameters

### Global Substra settings

| Name                             | Description                                                                                                                                                                        | Value                              |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `settings`                       | The settings to use for substra (`prod` or `dev`)                                                                                                                                  | `prod`                             |
| `config`                         | The configuration to use for substra                                                                                                                                               | `{}`                               |
| `organizationName`               | Current organization name                                                                                                                                                          | `owkin`                            |
| `DataSampleStorageInServerMedia` | If set to true, Datasamples which are registered by a "path" are kept on the "servermedias" volume. If set to `false` (default value), the datasample will be duplicated to MinIO. | `false`                            |
| `privateCa.enabled`              | Run the init container injecting the private CA certificate                                                                                                                        | `false`                            |
| `privateCa.image.repository`     | Private CA injector image                                                                                                                                                          | `substra-backend-ca-cert-injector` |
| `privateCa.image.tag`            | Private CA injector tag                                                                                                                                                            | `nil`                              |
| `privateCa.image.pullPolicy`     | Private CA injector pull policy                                                                                                                                                    | `IfNotPresent`                     |
| `privateCa.image.pullSecrets`    | Specify image pull secrets                                                                                                                                                         | `[]`                               |
| `privateCa.image.registry`       | The registery to pull the CA Cert Injector image                                                                                                                                   | `ghcr.io`                          |
| `privateCa.configMap.name`       | Name of the _ConfigMap_ containing the private CA certificate                                                                                                                      | `substra-private-ca`               |
| `privateCa.configMap.data`       | Certificate to add in the _ConfigMap_                                                                                                                                              | `nil`                              |
| `privateCa.configMap.fileName`   | Certificate filename in the _ConfigMap_                                                                                                                                            | `private-ca.crt`                   |
| `psp.create`                     | Create a _Pod Security Policy_ in the cluster. WARNING: PodSecurityPolicy is deprecated in Kubernetes 1.21 or later and unavailable in Kubernetes 1.25 or later                    | `true`                             |

### Server settings

| Name                                              | Description                                                                                                                                        | Value                                      |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `server.replicaCount`                             | Number of server replicas                                                                                                                          | `1`                                        |
| `server.defaultDomain`                            | The hostname and port of the backend. This address will be used as the assets `storage_address` field                                              | `localhost`                                |
| `server.subpath`                                  | The subpath under which the API is served                                                                                                          | `""`                                       |
| `server.commonHostDomain`                         | The common host under which the backend and frontend are served                                                                                    | `""`                                       |
| `server.uwsgiProcesses`                           | The number of uwsgi processes                                                                                                                      | `20`                                       |
| `server.uwsgiThreads`                             | The number of uwsgi threads                                                                                                                        | `10`                                       |
| `server.allowImplicitLogin`                       | Allow clients to get API tokens directly with username+password on the `/api-token-auth/` endpoint (ie `Client.login` in the Substra SDK)          | `true`                                     |
| `server.image.registry`                           | Substra backend server image registry                                                                                                              | `ghcr.io`                                  |
| `server.image.repository`                         | Substra backend server image repository                                                                                                            | `substra/substra-backend`                  |
| `server.image.tag`                                | Substra backend server image tag (defaults to AppVersion)                                                                                          | `nil`                                      |
| `server.image.pullPolicy`                         | Substra backend server image pull policy                                                                                                           | `IfNotPresent`                             |
| `server.image.pullSecrets`                        | Specify image pull secrets                                                                                                                         | `[]`                                       |
| `server.podSecurityContext.enabled`               | Enable security context                                                                                                                            | `true`                                     |
| `server.podSecurityContext.runAsUser`             | User ID for the pod                                                                                                                                | `1001`                                     |
| `server.podSecurityContext.runAsGroup`            | Group ID for the pod                                                                                                                               | `1001`                                     |
| `server.podSecurityContext.fsGroup`               | FileSystem group ID for the pod                                                                                                                    | `1001`                                     |
| `server.service.type`                             | Kubernetes Service type                                                                                                                            | `ClusterIP`                                |
| `server.service.port`                             | Server port                                                                                                                                        | `8000`                                     |
| `server.service.clusterIP`                        | _ClusterIP_ or `None` for headless service                                                                                                         | `""`                                       |
| `server.service.loadBalancerIP`                   | Load balancer IP if service type is `LoadBalancer`                                                                                                 | `""`                                       |
| `server.service.loadBalancerSourceRanges`         | Addresses that are allowed when service is `LoadBalancer`                                                                                          | `[]`                                       |
| `server.service.nodePort`                         | Specify the `nodePort` value for the `LoadBalancer` and `NodePort` service types                                                                   | `""`                                       |
| `server.service.externalIPs`                      | A list of IP addresses for which nodes in the cluster will also accept traffic for this service                                                    | `[]`                                       |
| `server.service.annotations`                      | Additional annotations for the _Service_ resource.                                                                                                 | `{}`                                       |
| `server.ingress.enabled`                          | Deploy an ingress for the substra backend server                                                                                                   | `false`                                    |
| `server.ingress.hostname`                         | Default host for the ingress ressource                                                                                                             | `substra.backend.local`                    |
| `server.ingress.pathType`                         | Ingress path type                                                                                                                                  | `ImplementationSpecific`                   |
| `server.ingress.path`                             | Path for the default host                                                                                                                          | `/`                                        |
| `server.ingress.extraPaths`                       | The list of extra paths to be created for the default host                                                                                         | `[]`                                       |
| `server.ingress.annotations`                      | Additional annotations for the Ingress resource.                                                                                                   | `{}`                                       |
| `server.ingress.extraHosts`                       | The list of additional hostnames to be covered with this ingress record                                                                            | `[]`                                       |
| `server.ingress.extraTls`                         | The tls configuration for hostnames to be coverred by the ingress                                                                                  | `[]`                                       |
| `server.ingress.ingressClassName`                 | _IngressClass_ that will be used to implement the Ingress                                                                                          | `nil`                                      |
| `server.resources`                                | Server container resources requests and limits                                                                                                     | `{}`                                       |
| `server.persistence.storageClass`                 | Specify the _StorageClass_ used to provision the volume. Or the default _StorageClass_ will be used. Set it to `-` to disable dynamic provisioning | `""`                                       |
| `server.persistence.servermedias.size`            | Servermedias volume size                                                                                                                           | `10Gi`                                     |
| `server.persistence.servermedias.existingClaim`   | use this PVC rather than creating a new one                                                                                                        | `nil`                                      |
| `server.livenessProbe.enabled`                    | Enable livenessProbe                                                                                                                               | `true`                                     |
| `server.livenessProbe.path`                       | Path of the HTTP service for checking the healthy state                                                                                            | `/liveness`                                |
| `server.livenessProbe.initialDelaySeconds`        | Initial delay seconds for livenessProbe                                                                                                            | `60`                                       |
| `server.livenessProbe.periodSeconds`              | Period seconds for livenessProbe                                                                                                                   | `45`                                       |
| `server.livenessProbe.timeoutSeconds`             | Timeout seconds for livenessProbe                                                                                                                  | `5`                                        |
| `server.livenessProbe.failureThreshold`           | Failure threshold for livenessProbe                                                                                                                | `6`                                        |
| `server.livenessProbe.successThreshold`           | Success threshold for livenessProbe                                                                                                                | `1`                                        |
| `server.readinessProbe.enabled`                   | Enable readinessProbe                                                                                                                              | `true`                                     |
| `server.readinessProbe.path`                      | Path of the HTTP service for checking the healthy state                                                                                            | `/readiness`                               |
| `server.readinessProbe.initialDelaySeconds`       | Initial delay seconds for readinessProbe                                                                                                           | `5`                                        |
| `server.readinessProbe.periodSeconds`             | Period seconds for readinessProbe                                                                                                                  | `30`                                       |
| `server.readinessProbe.timeoutSeconds`            | Timeout seconds for readinessProbe                                                                                                                 | `2`                                        |
| `server.readinessProbe.failureThreshold`          | Failure threshold for readinessProbe                                                                                                               | `3`                                        |
| `server.readinessProbe.successThreshold`          | Success threshold for readinessProbe                                                                                                               | `1`                                        |
| `server.metrics.enabled`                          | Start a prometheus exporter                                                                                                                        | `false`                                    |
| `server.metrics.image.registry`                   | Substra backend server Prometheus Exporter image registry                                                                                          | `ghcr.io`                                  |
| `server.metrics.image.repository`                 | Substra backend server Prometheus Exporter image repository                                                                                        | `substra/substra-backend-metrics-exporter` |
| `server.metrics.image.tag`                        | Substra backend server Prometheus Exporter image tag (defaults to AppVersion)                                                                      | `nil`                                      |
| `server.metrics.image.pullPolicy`                 | Substra backend server Prometheus Exporter image pull policy                                                                                       | `IfNotPresent`                             |
| `server.metrics.serviceMonitor.enabled`           | Create ServiceMonitor resource for scraping metrics using Prometheus Operator                                                                      | `false`                                    |
| `server.metrics.serviceMonitor.namespace`         | Namespace for the ServiceMonitor resource (defaults to the Release Namespace)                                                                      | `""`                                       |
| `server.metrics.serviceMonitor.interval`          | Interval at which metrics should be scraped                                                                                                        | `""`                                       |
| `server.metrics.serviceMonitor.scrapeTimeout`     | Timeout after which the scrape is ended                                                                                                            | `""`                                       |
| `server.metrics.serviceMonitor.relabelings`       | RelabelConfigs to apply to samples before scraping                                                                                                 | `[]`                                       |
| `server.metrics.serviceMonitor.metricRelabelings` | MetricRelabelConfigs to apply to samples before insertion                                                                                          | `[]`                                       |
| `server.metrics.serviceMonitor.honorLabels`       | Specify honorLabels parameter of the scrape endpoint                                                                                               | `false`                                    |

### Substra worker settings

| Name                                           | Description                                                                                                                                        | Value                     |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `worker.enabled`                               | Enable worker service                                                                                                                              | `true`                    |
| `worker.replicaCount`                          | Replica count for the worker service                                                                                                               | `1`                       |
| `worker.concurrency`                           | Maximum amount of tasks to process in parallel                                                                                                     | `1`                       |
| `worker.image.registry`                        | Substra backend worker image registry                                                                                                              | `ghcr.io`                 |
| `worker.image.repository`                      | Substra backend worker image repository                                                                                                            | `substra/substra-backend` |
| `worker.image.tag`                             | Substra backend worker image tag (defaults to AppVersion)                                                                                          | `nil`                     |
| `worker.image.pullPolicy`                      | Substra backend worker image pull policy                                                                                                           | `IfNotPresent`            |
| `worker.image.pullSecrets`                     | Specify image pull secrets                                                                                                                         | `[]`                      |
| `worker.podSecurityContext.enabled`            | Enable security context                                                                                                                            | `true`                    |
| `worker.podSecurityContext.runAsUser`          | User ID for the pod                                                                                                                                | `1001`                    |
| `worker.podSecurityContext.runAsGroup`         | Group ID for the pod                                                                                                                               | `1001`                    |
| `worker.podSecurityContext.fsGroup`            | FileSystem group ID for the pod                                                                                                                    | `1001`                    |
| `worker.resources`                             | Worker container resources requests and limits                                                                                                     | `{}`                      |
| `worker.nodeSelector`                          | Node labels for pod assignment                                                                                                                     | `{}`                      |
| `worker.tolerations`                           | Toleration labels for pod assignment                                                                                                               | `[]`                      |
| `worker.affinity`                              | Affinity settings for pod assignment, ignored if `DataSampleStorageInServerMedia` is `true`                                                        | `{}`                      |
| `worker.rbac.create`                           | Create a role and service account for the worker                                                                                                   | `true`                    |
| `worker.persistence.storageClass`              | Specify the _StorageClass_ used to provision the volume. Or the default _StorageClass_ will be used. Set it to `-` to disable dynamic provisioning | `""`                      |
| `worker.persistence.size`                      | The size of the volume. The size of this volume should be sufficient to store many assets.                                                         | `10Gi`                    |
| `worker.computePod.maxStartupWaitSeconds`      | Set the maximum amount of time we will wait for the compute pod to be ready                                                                        | `300`                     |
| `worker.computePod.securityContext.fsGroup`    | Set the filesystem group for the Compute pod                                                                                                       | `1001`                    |
| `worker.computePod.securityContext.runAsUser`  | Set the user for the Compute pod                                                                                                                   | `1001`                    |
| `worker.computePod.securityContext.runAsGroup` | Set the group for the Compute pod                                                                                                                  | `1001`                    |
| `worker.events.enabled`                        | Enable event service                                                                                                                               | `true`                    |
| `worker.events.image.registry`                 | Substra event app image registry                                                                                                                   | `ghcr.io`                 |
| `worker.events.image.repository`               | Substra event app image repository                                                                                                                 | `substra/substra-backend` |
| `worker.events.image.tag`                      | Substra event app image tag (defaults to AppVersion)                                                                                               | `nil`                     |
| `worker.events.image.pullPolicy`               | Substra event app image pull policy                                                                                                                | `IfNotPresent`            |
| `worker.events.image.pullSecrets`              | Specify image pull secrets                                                                                                                         | `[]`                      |
| `worker.events.podSecurityContext.enabled`     | Enable security context                                                                                                                            | `true`                    |
| `worker.events.podSecurityContext.runAsUser`   | User ID for the pod                                                                                                                                | `1001`                    |
| `worker.events.podSecurityContext.runAsGroup`  | Group ID for the pod                                                                                                                               | `1001`                    |
| `worker.events.podSecurityContext.fsGroup`     | FileSystem group ID for the pod                                                                                                                    | `1001`                    |
| `worker.events.nodeSelector`                   | Node labels for pod assignment                                                                                                                     | `{}`                      |
| `worker.events.tolerations`                    | Toleration labels for pod assignment                                                                                                               | `[]`                      |
| `worker.events.affinity`                       | Affinity settings for pod assignment                                                                                                               | `{}`                      |
| `worker.events.rbac.create`                    | Create a role and service account for the event app                                                                                                | `true`                    |
| `worker.events.serviceAccount.create`          | Create a service account for the event app                                                                                                         | `true`                    |
| `worker.events.serviceAccount.name`            | The name of the ServiceAccount to use                                                                                                              | `""`                      |

### Substra periodic tasks worker settings

| Name                                            | Description                                                        | Value                     |
| ----------------------------------------------- | ------------------------------------------------------------------ | ------------------------- |
| `schedulerWorker.enabled`                       | Enable scheduler worker service                                    | `true`                    |
| `schedulerWorker.replicaCount`                  | Replica count for the periodic tasks worker                        | `1`                       |
| `schedulerWorker.image.registry`                | Substra backend tasks scheduler image registry                     | `ghcr.io`                 |
| `schedulerWorker.image.repository`              | Substra backend tasks scheduler image repository                   | `substra/substra-backend` |
| `schedulerWorker.image.tag`                     | Substra backend tasks scheduler image tag (defaults to AppVersion) | `nil`                     |
| `schedulerWorker.image.pullPolicy`              | Substra backend task scheduler image pull policy                   | `IfNotPresent`            |
| `schedulerWorker.image.pullSecrets`             | Specify image pull secrets                                         | `[]`                      |
| `schedulerWorker.nodeSelector`                  | Node labels for pod assignment                                     | `{}`                      |
| `schedulerWorker.tolerations`                   | Toleration labels for pod assignment                               | `[]`                      |
| `schedulerWorker.affinity`                      | Affinity settings for pod assignment                               | `{}`                      |
| `schedulerWorker.resources`                     | Scheduler container resources requests and limits                  | `{}`                      |
| `schedulerWorker.podSecurityContext.enabled`    | Enable security context                                            | `true`                    |
| `schedulerWorker.podSecurityContext.runAsUser`  | User ID for the pod                                                | `1001`                    |
| `schedulerWorker.podSecurityContext.runAsGroup` | Group ID for the pod                                               | `1001`                    |
| `schedulerWorker.podSecurityContext.fsGroup`    | FileSystem group ID for the pod                                    | `1001`                    |

### Celery task scheduler settings

| Name                                      | Description                                                        | Value                     |
| ----------------------------------------- | ------------------------------------------------------------------ | ------------------------- |
| `scheduler.enabled`                       | Enable scheduler service                                           | `true`                    |
| `scheduler.replicaCount`                  | Replica count for the scheduler server                             | `1`                       |
| `scheduler.image.registry`                | Subsra backend tasks scheduler image registry                      | `ghcr.io`                 |
| `scheduler.image.repository`              | Substra backend tasks scheduler image repository                   | `substra/substra-backend` |
| `scheduler.image.tag`                     | Substra backend tasks scheduler image tag (defaults to AppVersion) | `nil`                     |
| `scheduler.image.pullPolicy`              | Substra backend task scheduler image pull policy                   | `IfNotPresent`            |
| `scheduler.image.pullSecrets`             | Specify image pull secrets                                         | `[]`                      |
| `scheduler.resources`                     | Scheduler container resources requests and limits                  | `{}`                      |
| `scheduler.nodeSelector`                  | Node labels for pod assignment                                     | `{}`                      |
| `scheduler.tolerations`                   | Toleration labels for pod assignment                               | `[]`                      |
| `scheduler.affinity`                      | Affinity settings for pod assignment                               | `{}`                      |
| `scheduler.podSecurityContext.enabled`    | Enable security context                                            | `true`                    |
| `scheduler.podSecurityContext.runAsUser`  | User ID for the pod                                                | `1001`                    |
| `scheduler.podSecurityContext.runAsGroup` | Group ID for the pod                                               | `1001`                    |
| `scheduler.podSecurityContext.fsGroup`    | FileSystem group ID for the pod                                    | `1001`                    |

### Builder settings

| Name                                    | Description                                                                                                                                        | Value                     |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `builder.replicaCount`                  | Number of builder replicas                                                                                                                         | `1`                       |
| `builder.enabled`                       | Enable worker service                                                                                                                              | `true`                    |
| `builder.replicaCount`                  | Replica count for the worker service                                                                                                               | `1`                       |
| `builder.concurrency`                   | Maximum amount of tasks to process in parallel                                                                                                     | `1`                       |
| `builder.image.registry`                | Substra backend server image registry                                                                                                              | `ghcr.io`                 |
| `builder.image.repository`              | Substra backend server image repository                                                                                                            | `substra/substra-backend` |
| `builder.image.tag`                     | Substra backend server image tag (defaults to AppVersion)                                                                                          | `nil`                     |
| `builder.image.pullPolicy`              | Substra backend server image pull policy                                                                                                           | `IfNotPresent`            |
| `builder.image.pullSecrets`             | Specify image pull secrets                                                                                                                         | `[]`                      |
| `builder.podSecurityContext.enabled`    | Enable security context                                                                                                                            | `true`                    |
| `builder.podSecurityContext.runAsUser`  | User ID for the pod                                                                                                                                | `1001`                    |
| `builder.podSecurityContext.runAsGroup` | Group ID for the pod                                                                                                                               | `1001`                    |
| `builder.podSecurityContext.fsGroup`    | FileSystem group ID for the pod                                                                                                                    | `1001`                    |
| `builder.resources`                     | Builder container resources requests and limits                                                                                                    | `{}`                      |
| `builder.nodeSelector`                  | Node labels for pod assignment                                                                                                                     | `{}`                      |
| `builder.tolerations`                   | Toleration labels for pod assignment                                                                                                               | `[]`                      |
| `builder.affinity`                      | Affinity settings for pod assignment, ignored if `DataSampleStorageInServerMedia` is `true`                                                        | `{}`                      |
| `builder.persistence.storageClass`      | Specify the _StorageClass_ used to provision the volume. Or the default _StorageClass_ will be used. Set it to `-` to disable dynamic provisioning | `""`                      |
| `builder.persistence.size`              | The size of the volume.                                                                                                                            | `10Gi`                    |
| `builder.rbac.create`                   | Create a role and service account for the builder                                                                                                  | `true`                    |

### Substra container registry settings

| Name                            | Description                                                                                     | Value       |
| ------------------------------- | ----------------------------------------------------------------------------------------------- | ----------- |
| `containerRegistry.local`       | Whether the registry is exposed as a _nodePort_ and located in the same _Namespace_ as Substra. | `true`      |
| `containerRegistry.host`        | Hostname of the container registry                                                              | `127.0.0.1` |
| `containerRegistry.port`        | Port of the container registry                                                                  | `32000`     |
| `containerRegistry.scheme`      | Communication scheme of the container registry                                                  | `http`      |
| `containerRegistry.pullDomain`  | Hostname from which the cluster should pull container images                                    | `127.0.0.1` |
| `containerRegistry.prepopulate` | Images to add to the container registry                                                         | `[]`        |

### Api event app settings

| Name                                       | Description                                          | Value                     |
| ------------------------------------------ | ---------------------------------------------------- | ------------------------- |
| `api.events.enabled`                       | Enable event service                                 | `true`                    |
| `api.events.image.registry`                | Substra event app image registry                     | `ghcr.io`                 |
| `api.events.image.repository`              | Substra event app image repository                   | `substra/substra-backend` |
| `api.events.image.tag`                     | Substra event app image tag (defaults to AppVersion) | `nil`                     |
| `api.events.image.pullPolicy`              | Substra event app image pull policy                  | `IfNotPresent`            |
| `api.events.image.pullSecrets`             | Specify image pull secrets                           | `[]`                      |
| `api.events.podSecurityContext.enabled`    | Enable security context                              | `true`                    |
| `api.events.podSecurityContext.runAsUser`  | User ID for the pod                                  | `1001`                    |
| `api.events.podSecurityContext.runAsGroup` | Group ID for the pod                                 | `1001`                    |
| `api.events.podSecurityContext.fsGroup`    | FileSystem group ID for the pod                      | `1001`                    |
| `api.events.nodeSelector`                  | Node labels for pod assignment                       | `{}`                      |
| `api.events.tolerations`                   | Toleration labels for pod assignment                 | `[]`                      |
| `api.events.affinity`                      | Affinity settings for pod assignment                 | `{}`                      |
| `api.events.rbac.create`                   | Create a role and service account for the event app  | `true`                    |
| `api.events.serviceAccount.create`         | Create a service account for the event app           | `true`                    |
| `api.events.serviceAccount.name`           | The name of the ServiceAccount to use                | `""`                      |

### Orchestrator settings

| Name                                                      | Description                                                                                                                    | Value                |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------- |
| `orchestrator.host`                                       | The orchestrator gRPC endpoint                                                                                                 | `orchestrator.local` |
| `orchestrator.port`                                       | The orchestrator gRPC port                                                                                                     | `9000`               |
| `orchestrator.tls.enabled`                                | Enable TLS for the gRPC endpoint                                                                                               | `false`              |
| `orchestrator.tls.cacert`                                 | A configmap containing the orchestrator CA certificate. Use this if your orchestrator uses a private CA.                       | `nil`                |
| `orchestrator.tls.mtls.enabled`                           | Enable client verification for the orchestrator gRPC endpoint                                                                  | `false`              |
| `orchestrator.tls.mtls.clientCertificate`                 | A secret containing the client certificate `tls.crt` and private key `tls.key`                                                 | `nil`                |
| `orchestrator.mspID`                                      | current organization name on the Orchestrator                                                                                  | `OwkinPeerMSP`       |
| `orchestrator.channels[0].mychannel.restricted`           | Make this channel restricted to a single organization. The server will fail if there is more than one instance in this channel | `false`              |
| `orchestrator.channels[0].mychannel.model_export_enabled` | Allow logged-in users to download models trained on this organization                                                          | `false`              |

### Kaniko settings

| Name                                    | Description                                                                                                                                        | Value                     |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `kaniko.image.registry`                 | Kaniko image registry                                                                                                                              | `gcr.io`                  |
| `kaniko.image.repository`               | Kaniko image repository                                                                                                                            | `kaniko-project/executor` |
| `kaniko.image.tag`                      | Kaniko image tag                                                                                                                                   | `v1.8.1`                  |
| `kaniko.mirror`                         | If set to `true` pull base images from the local registry.                                                                                         | `false`                   |
| `kaniko.dockerConfigSecretName`         | A Docker config to use for pulling base images                                                                                                     | `nil`                     |
| `kaniko.cache.warmer.image.registry`    | Kaniko cache warmer registry                                                                                                                       | `gcr.io`                  |
| `kaniko.cache.warmer.image.repository`  | Kaniko cache warmer repository                                                                                                                     | `kaniko-project/warmer`   |
| `kaniko.cache.warmer.image.tag`         | Kaniko cache warmer image tag                                                                                                                      | `v1.8.1`                  |
| `kaniko.cache.warmer.cachedImages`      | A list of docker images to warmup the Kaniko cache                                                                                                 | `[]`                      |
| `kaniko.cache.persistence.storageClass` | Specify the _StorageClass_ used to provision the volume. Or the default _StorageClass_ will be used. Set it to `-` to disable dynamic provisioning | `""`                      |
| `kaniko.cache.persistence.size`         | The size of the volume.                                                                                                                            | `10Gi`                    |

### Account operator settings

| Name                                       | Description                                                                                        | Value |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------- | ----- |
| `addAccountOperator.outgoingOrganizations` | Outgoind organizations credentials for substra backend organization-to-organization communications | `[]`  |
| `addAccountOperator.incomingOrganizations` | Incoming organizations credentials for substra backend organization-to-organization communications | `[]`  |
| `addAccountOperator.users`                 | A list of administrators users who can log into the substra backend server with admin privileges   | `[]`  |

### Single Sign-On through OpenID Connect

Uses the authorization code flow.

By default, `oidc.users.useRefreshToken` is enabled. This makes sure the user still has an account at the identity provider, without damaging user experience.

The way it works is that a OIDC user that spent more than `oidc.users.loginValidityDuration` since their last login must undergo a refresh to keep using their access tokens -- but these refreshes are done in the background if `oidc.users.useRefreshToken` is enabled (otherwise a new manual authorization is necessary). The identity provider must support `offline_access` and configuration discovery.

With this option active, you can set `oidc.users.loginValidityDuration` to low values (minutes).

Else, you must strike a balance: longer durations are more convenient, but risk users having continued access even though their account has been disabled.


| Name                                    | Description                                                                                                                                                     | Value   |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| `oidc.enabled`                          | Whether to enable OIDC authentication                                                                                                                           | `false` |
| `oidc.clientSecretName`                 | The name of a secret containing the keys `OIDC_RP_CLIENT_ID` and `OIDC_RP_CLIENT_SECRET` (client ID and secret, typically issued by the provider)               | `nil`   |
| `oidc.provider.url`                     | The identity provider URL (with scheme).                                                                                                                        | `nil`   |
| `oidc.provider.displayName`             | The name of the provider as displayed in the interface ("Sign in with X")                                                                                       | `nil`   |
| `oidc.provider.endpoints.authorization` | Typically https://provider/auth                                                                                                                                 | `nil`   |
| `oidc.provider.endpoints.token`         | Typically https://provider/token                                                                                                                                | `nil`   |
| `oidc.provider.endpoints.user`          | Typically https://provider/me                                                                                                                                   | `nil`   |
| `oidc.provider.jwksUri`                 | Typically https://provider/jwks. Only required for public-key-based signing algorithms. If not given, read from `/.well-known/openid-configuration` at startup. | `nil`   |
| `oidc.signAlgo`                         | Either RS256 or HS256                                                                                                                                           | `RS256` |
| `oidc.users.useRefreshToken`            | Attempt to refresh user info in the background.                                                                                                                 | `true`  |
| `oidc.users.loginValidityDuration`      | How long a user account is valid after an OIDC login, in seconds                                                                                                | `3600`  |
| `oidc.users.channel`                    | The channel to assign OIDC users to (mandatory)                                                                                                                 | `nil`   |
| `oidc.users.requireApproval`            | Activate the user approval. A user using the OIDC login for the first time will need approval from an admin. It is not compatible with default channel          | `false` |
| `oidc.users.appendDomain`               | As usernames are assigned based on e-mail address, whether to suffix user names with the email domain (john.doe@example.com would then be `john-doe-example`)   | `false` |

### Database connection settings

| Name                                  | Description                                                                                                 | Value      |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------- |
| `database.auth.database`              | what DB to connect to                                                                                       | `substra`  |
| `database.auth.username`              | what user to connect as                                                                                     | `postgres` |
| `database.auth.password`              | what password to use for connecting                                                                         | `postgres` |
| `database.auth.credentialsSecretName` | An alternative to giving username and password; must have `DATABASE_USERNAME` and `DATABASE_PASSWORD` keys. | `nil`      |
| `database.host`                       | Hostname of the database to connect to (defaults to local)                                                  | `nil`      |
| `database.port`                       | Port of an external database to connect to                                                                  | `5432`     |

### PostgreSQL settings

Database included as a subchart used by default.

See Bitnami documentation: https://bitnami.com/stack/postgresql/helm

| Name                 | Description                                                | Value  |
| -------------------- | ---------------------------------------------------------- | ------ |
| `postgresql.enabled` | Deploy a PostgreSQL instance along the backend for its use | `true` |

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

### Data sample storage

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

### Database

#### Internal

If you change connection settings for the internal database such as credentials, don't forget to also update the ones used for connecting:

```yaml
database:
  auth:
    password: abcd1234 # the password the backend will use

postgresql:
  auth:
    password: abcd1234 # the password the database expects
```

(you could use YAML anchors for this)

#### External

The backend uses a PostgreSQL database. By default it will deploy one as a subchart. To avoid this behavior, set the appropriate values:

```yaml
database:
  host: my.database.host

  auth:
    username: my-user
    password: aStrongPassword
    database: orchestrator

postgresql:
  enabled: false
```
