# Substra-Backend [![Python](https://github.com/Substra/substra-backend/actions/workflows/python.yml/badge.svg)](https://github.com/Substra/substra-backend/actions/workflows/python.yml) [![Helm](https://github.com/Substra/substra-backend/actions/workflows/helm.yml/badge.svg)](https://github.com/Substra/substra-backend/actions/workflows/helm.yml) [![Build substra backend image](https://github.com/Substra/substra-backend/actions/workflows/container-image-backend.yml/badge.svg)](https://github.com/Substra/substra-backend/actions/workflows/container-image-backend.yml)

Backend of the Substra platform

## Running a development instance

This section details how you can get started on running a local substra backend. For this you will need a running Kubernetes cluster and the [orchestrator](https://github.com/Substra/orchestrator) deployed in this cluster.

If you want to run the substra-backend with Skaffold you will need to add the twuni and bitnami helm repos:
```sh
helm repo add twuni https://helm.twun.io
helm repo add bitnami https://charts.bitnami.com/bitnami
```

To launch the substra backend:
```sh
skaffold dev
```
or
```sh
skaffold run
```

This will spawn several pods in two different namespaces to simulate several organizations: 'org-1' and 'org-2'.
Each organization will have:
- Postgres database
- Redis message broker
- Docker registry
- Kaniko cache warmer
- [Celery beat](./charts/substra-backend/templates/deployment-scheduler.yaml)
- 2 celery workers (a [worker](./charts/substra-backend/templates/statefulset-worker.yaml) executing tasks and a [scheduler](./charts/substra-backend/templates/deployment-scheduler-worker.yaml) restarting hanging tasks and performing cleanup tasks)
- a [_Job_](./charts/substra-backend/templates/job-migrations.yaml) to run migrations and add accounts.
- the [API backend](./charts/substra-backend/templates/deployment-server.yaml)
- the [events backend](./charts/substra-backend/templates/deployment-events.yaml) converting events from the orchestrator into celery tasks

### VSCode

For Visual Studio resources for substra-backend, see [this page](./docs/vscode.md)

### Use dev profile

Use `skaffold [run|dev] -p dev` in order to take advantage of:
- Pre-installed dev tools: debugger, profiler
- Test modules: fixtures, assets factory, utils
- Run application container as root: install packages, edit files, restart services

### Use debugger

Add a breakpoint, then attach to the `backend-server` container.

```sh
kubectl attach -it -n org-1 $(kubectl get pods -o=name -n org-1 -l app.kubernetes.io/name=substra-backend-server)
```

Use `Ctrl+p` then `Ctrl+q` to detach without killing the container.

See: https://docs.python.org/fr/3/library/pdb.html

### Running on multiple kubernetes nodes

The backend can be deployed on a kubernete cluster running more than one kubernetes node.

To run the worker and the server on two different nodes:
Label the nodes:
```sh
kubectl label nodes <node_name> server=true
kubectl label nodes <node_name> worker=true
```

Deploy the backend with:
    - `skaffold run -p add-worker-server-node-selectors` to run 1 server pod and 1 worker pod on 2 separate kubernetes nodes. The nodes need to be labelled (see `add-worker-server-node-selectors.yaml`)
    - `skaffold run -p spread-workers` to spread the workers across the `x` different nodes.

You can draw from this documentation to set up the config according to your needs: number of kubernetes nodes, number of worker replicas, way to spread workers across the kubernetes nodes.

### Run with servermedia profile

To enable storing datasamples on the servermedia PVC instead of minio, use `skaffold run -p servermedias`. The PVs need to be created prior to requesting them inside the PVC:

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: backend-org-1-substra-backend-servermedias
  labels:
    app.kubernetes.io/instance: < Release.Name > # here it will be backend-org-1
spec:
  storageClassName: manual
  persistentVolumeReclaimPolicy: Delete # You can also use "Retain" or "Recycle"
  capacity:
    storage: 20Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/tmp/org-1/servermedias"

---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: backend-org-2-substra-backend-servermedias
  labels:
    app.kubernetes.io/instance: < Release.Name > # here it will be backend-org-2
spec:
  storageClassName: manual
  persistentVolumeReclaimPolicy: Delete # You can also use "Retain" or "Recycle"
  capacity:
    storage: 20Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/tmp/org-2/servermedias"
```

## Django management

To get access to the [Django management tool](https://docs.djangoproject.com/en/2.2/ref/django-admin), spawn a shell in the running container:
```sh
kubectl -n org-1 exec -i -t $(kubectl -n org-1 get pods -l=app.kubernetes.io/name=substra-backend-server -o name) -c substra-backend -- /bin/bash
```

This will also gives you access to the [celery CLI](https://docs.celeryproject.org/en/stable/reference/cli.html). You can issue `celery inspect active_queues` to examine consumed queues.

## Running substrapp in a venv
If your useCase only involves the django app (not the eventapp, nor the compute engine for instance), you may easily run it and serve the API without a k8s cluster.
See [this page](./docs/localdev.md)


## Execute unit tests

Unit tests require to have a running postgres instance.

If it is not already running, you could start a new DB, using the command below.
This command will only work if you have a local docker daemon running.
It is recommended to use the same version as the one defined in the charts.

```sh
make db
```

Alternatively, you could also set the environment variables defined in `backend.settings.test` to provide any DB info.

```sh
export BACKEND_DB_NAME=<db_name> \
    BACKEND_DB_USER=<db_user> \
    BACKEND_DB_PWD=<db_password> \
    BACKEND_DB_HOST=<db_host> \
    BACKEND_DB_PORT=<db_port>
```

Make sure you have the requirements installed:
```sh
pip install -r backend/dev-requirements.txt
```

Then launch unit tests:
```sh
make test
```

A coverage report can be obtained with:
```sh
make coverage
```

Should you prefer an HTML report, you can use `coverage html` from the `backend` directory.

## Updating gRPC definitions

Assuming you have cloned the [orchestrator](https://github.com/owkin/orchestrator) in `<orchestrator_root>`:
```sh
cd backend
ORCHESTRATOR_ROOT=<orchestrator_root> make orchestrator-grpc
```

Note that this requires grpcio-tools, which should be available if you installed requirements (see above).

## Accessing the app

On deployment, several user accounts are created (for [./values/backend-org-1.yaml](org1) and [./values/backend-org-2.yaml](org2)).

The sample credentials for org1 are:
- user: `org-1`
- pass: `p@sswr0d44`

Provided you have correctly setup your [network configuration](https://doc.substra.ai/setup/local_install_skaffold.html#network), you can use them to access the exposed API at http://substra-backend.org-1.com/

## Compatibility

Make sure you deploy this backend with a compatible ecosystem (chaincode, hlf-k8s, etc).
Always refer to the [compatibility table](https://github.com/SubstraFoundation/substra#compatibility-table).

The recommended way to run a specific version (0.1.6) of substra-backend is to execute:

```bash
SUBSTRA_BACKEND_VERSION=0.1.6
git checkout $SUBSTRA_BACKEND_VERSION
skaffold deploy --images substrafoundation/substra-backend:$SUBSTRA_BACKEND_VERSION
```

## Code formatting

You can opt into auto-formatting of code on pre-commit using [Black](https://github.com/psf/black).

This relies on hooks managed by [pre-commit](https://pre-commit.com/), which you can set up as follows.

Install [pre-commit](https://pre-commit.com/), then run:

```sh
pre-commit install
```

## Companion repositories

The Substra platform is built from several components (see the [architecture](https://doc.substra.ai/architecture.html) documentation for a comprehensive overview):

- [hlf-k8s](https://github.com/Substra/hlf-k8s) is the implementation of Hyperledger Fabric on which this backend rely
- [orchestrator](https://github.com/Substra/orchestrator) contains the orchestration logic of a federated learning deployment
- [substra-frontend](https://github.com/Substra/substra-frontend) is the frontend consuming the API exposed by the backend
- [substra-tests](https://github.com/Substra/substra-tests) is the Substra end to end test suite

## License

This project is developed under the Apache License, Version 2.0 (Apache-2.0), located in the [LICENSE](./LICENSE) file.


### Running the backend on arm64 architecture (apple chip)


Tested with:
    * python 3.9.4
    * pip 22.0.4

Currently only the dev mode is supported with this architecture.

1. uwsgi

When using pyenv-virtualenv, the python library might not be linked correctly into the python directory. Adding a manual link `sudo ln -s` to the expected folder will solve the issue:
```
sudo ln -s /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9.4/lib/python3.9/config-3.9-darwin <INSERT YOUR NOT-FOUND-PATH HERE WITHOUT libpython3.8.a FILENAME>
```

2. Deploy with `skaffold run -p dev,arm64`
