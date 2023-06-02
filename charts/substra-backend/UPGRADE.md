## unreleased

## 23.0.0

The settings for the integrated PostgreSQL instance are now under `integrated-postgresql` rather than just `postgresql`. `postgresql` is now for connection details to any database.

## 21.0.0

If you want to keep persistence disabled for postgresql you will need to set the key `postgresql.primary.persistence.enabled` to `false` in your values.

## 19.0.0

Change the format of `image.pullSecrets`:
```yaml
# before:
image:
  pullSecrets:
    - docker-secret
# after:
image:
  pullSecrets:
    - name: docker-secret
```

## 18.1.0

Rename the key `addAccountOperator.outgoingNodes` to `addAccountOperator.outgoingOrganizations`.
Rename the key `addAccountOperator.incomingNodes` to `addAccountOperator.incomingOrganizations`.

## 16.0.0

Rename the key `worker.rbac.enable` to `worker.rbac.create` in your values file

## 15.0.0

Apply changes from [minio 8](https://github.com/bitnami/charts/tree/master/bitnami/minio#to-800) and [minio 9](https://github.com/bitnami/charts/tree/master/bitnami/minio#to-900).

## 14.0.0

See [CHANGELOG.md](./CHANGELOG.md#14.0.0).
Metrics, datamanagers and algos are now stored in Minio.
Minio persistent size should be increased to support the additional storage from the previous metrics, datamanagers and algos volumes.
After upgrading from 13.x.x to 14.0.0 the assets will need to be reuploaded into the platform.

## 13.0.0

Almost all the sections in the values files were re-done.
We would suggest starting from a clean sheet. If you still want to migrate, here is some key values you could update.

- `backend` is now `server`
- `celeryworker` is now `worker`
- `scheduler` is now `schedulerWorker`
- `celerybeat` is now `scheduler`

All the application configuration that was created using multiple values is now set under a unique key `config`. You can see more about the removed keys in the `CHANGELOG.md` file.
## 12.0.0
- Note that the objectives volume is renamed metrics

## 11.0.0

1. Set `hooks.deleteWorkerPvc.enabled` to the desired value. Note that delete hooks are triggered only when deploying with helm.
2. Optional: set `celeryworker.replicaCount` value
3. Optional: on multi node set up. Set up the way pods are scheduled across kubernetes nodes either with affinity or anti-affinity, see the [spread workers across nodes](../../values/spread-workers.yaml) for the full configuration, or using `nodeSelector` and labelling.

## 10.0.0
- Note that the kaniko cache volume is now configurable via `backend.kaniko.persistence` fields.

## 9.0.0

1. Persistence. In this order:
    - Remove `persistence.datasamples`.
    - Remove `persistence.models`.
    - Remove `persistence.computeplan`.
    - Remove `persistence.local`.
    - Rename `persistence.volumes.subtuple` to `celeryworker.persistence.volumes.subtuple`. `subtuple` should be at least as large as the MinIO disk (see below).
    - Rename `persistence` to `backend.persistence`
    - For each volume in `backend.persistence.volumes`: remove `[volume].readOnly`
    - For each volume in `celeryworker.persistence.volumes`: remove `[volume].readOnly`.
    - If you wish to use `hostPath` for the volumes defined under `celeryworker.persistence`, do so in the `celery.persistence` field.

    - Here is an example of the diff for a `backend` volume:
        ```yaml
            # __before__ (8.x.x)
            persistence:
                volumes:
                    algos:
                        size: "10Gi"
                        readOnly:
                            server: false
                            worker: true
            # __after__ (9.x.x)
            backend:
                persistence:
                    volumes:
                        algos:
                            size: "10Gi"
        ```
    - Here is an example of the diff for a `celeryworker` volume:
        ```yaml
            # __before__ (8.x.x)
            persistence:
                volumes:
                    subtuple:
                        size: "10Gi"
                        readOnly:
                            server: false
                            worker: true
            # __after__ (9.x.x)
            celeryworker:
                persistence:
                    volumes:
                        subtuple:
                            size: "10Gi"
        ```

2. Configure MinIO:
    - Note that a chart dependency to MinIO was added.
    - Here is the [MinIO chart](https://github.com/bitnami/charts/tree/master/bitnami/minio#persistence-parameters).
    - Set the accessKey (`minio.accessKey.password`) and secretKey (`minio.secretKey.password`).
    - Set `minio.persistence.*` to the desired values. Note that `size` should be at least equal to the size of the `datasamples` PV + the size of the `models` PV (both of which were deleted in the steps above).

3. _In a context where there is only one kubernetes node_: it is possible to set `celeryworker.persistence.servermedias.enableDatasampleStorage` to `true`. See [more detailed explanation](./README.md#datasample-storage).


## 5.0.0

This version adds support for Kubernetes 1.22. This required some changes to the Ingress.

If you had a single host and a single path for your ingress:
- move `backend.ingress.hosts[0].host` to `backend.ingress.hostname`
- move `backend.ingress.hosts[0].paths[0]` to `backend.ingress.path`

If you had multiple hosts you can proceed as for a single host for your first host and then add your other hosts to `backend.ingress.extraHosts`.

The other significant change is a rename from `backend.ingress.tls` to `backend.ingress.extraTls`, the data structure inside is the same.


## 4.0.0

 - Add orchestrator connection (grpc + rabbitmq). You need to handle certificates generation if you want to use tls or mutual tls with those connection


## 3.0.0

- Replace `rabbitmq.rabbitmq` with `rabbitmq.auth`
