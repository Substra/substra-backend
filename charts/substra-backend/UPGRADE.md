## unreleased

## 12.0.5

- rename `SCHEDULE_TASK_PERIOD` to `CELERYBEAT_SCHEDULE_TASK_PERIOD`
- rename `FLUSH_EXPIRED_TOKENS_TASK_PERIOD` to `CELERYBEAT_FLUSH_EXPIRED_TOKENS_TASK_PERIOD`
- rename `MAXIMUM_IMAGES_TTL`to `CELERYBEAT_MAXIMUM_IMAGES_TTL`

## 12.0.0
- Note that the objectives volume is renamed metrics

## 11.0.0

1. Set `hooks.deleteWorkerPvc.enabled` to the desired value. Note that delete hooks are triggered only when deploying with helm.
2. Optional: set `celeryworker.replicaCount` value
3. Optional: on multi node set up. Set up the way pods are scheduled across kubernetes nodes either with affinity or anti-affinity, see the [spread workers accross nodes](../../values/spread-workers.yaml) for the full configuration, or using `nodeSelector` and labelling.

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
