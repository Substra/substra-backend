# Substra-Backend [![Python](https://github.com/SubstraFoundation/substra-backend/workflows/Python/badge.svg)](https://github.com/SubstraFoundation/substra-backend/actions?query=workflow%3APython) [![Helm](https://github.com/SubstraFoundation/substra-backend/workflows/Helm/badge.svg)](https://github.com/SubstraFoundation/substra-backend/actions?query=workflow%3AHelm) [![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/substrafoundation/substra-backend)](https://hub.docker.com/r/substrafoundation/substra-backend/builds)

Backend of the Substra platform

## Running a development instance

For the local installation of substra-backend (and companions), please refer to the [setup documentation](https://doc.substra.ai/setup/local_install_skaffold.html).

With [hlf-k8s](https://github.com/SubstraFoundation/hlf-k8s) already running and requirements fulfilled, this should boils down to:
```sh
skaffold dev
```

This will spawn several pods in two different namespaces to simulate several organizations: 'org-1' and 'org-2'.
Each organization will have:
- Postgres database
- RabbitMQ message broker
- Docker registry
- Kaniko cache warmer
- [Celery beat](./charts/substra-backend/templates/deployment-celerybeat.yaml)
- 2 celery workers (a [worker](./charts/substra-backend/templates/deployment-worker.yaml) executing tasks and a [scheduler](./charts/substra-backend/templates/deployment-scheduler.yaml) restarting hanging tasks)
- an [operator pattern to add accounts](./charts/substra-backend/templates/add-account-operator.yaml)
- the [API backend](./charts/substra-backend/templates/deployment-server.yaml)
- the [events backend](./charts/substra-backend/templates/deployment-events.yaml) converting events from the chaincode into celery tasks

### Use debugger

Add a breakpoint, then attach to the `backend-server` container.

```sh
kubectl attach -it -n org-1 $(kubectl get pods -o=name -n org-1 -l app.kubernetes.io/name=substra-backend-server)
```

Use `Ctrl+p` then `Ctrl+q` to detach without killing the container.

See: https://docs.python.org/fr/3/library/pdb.html

### Running on multiple kubernetes nodes

The backend can be deployed on a kubernete cluster running more than one kubernetes node.

To run the worker and the server on two different nodes (requires the nodes to be labelled [see wiki](`https://github.com/owkin/connect-backend/wiki/Running-the-backend-on-Multinode`)

Deploy the backend with:
    - `skaffold run -p add-worker-server-node-selectors` to run 1 server pod and 1 worker pod on 2 separate kubernetes nodes. The nodes need to be labelled (see `add-worker-server-node-selectors.yaml`)
    - `skaffold run -p spread-workers` to spread the workers across the `x` different nodes.

You can draw from this documentation to set up the config according to your needs: number of kubernetes nodes, number of worker replicas, way to spread workers across the kubernetes nodes.

## Django management

To get access to the [Django management tool](https://docs.djangoproject.com/en/2.2/ref/django-admin), spawn a shell in the running container:
```sh
kubectl -n org-1 exec -i -t $(kubectl -n org-1 get pods -l=app.kubernetes.io/name=substra-backend-server -o name) -c substra-backend -- /bin/bash
```

This will also gives you access to the [celery CLI](https://docs.celeryproject.org/en/stable/reference/cli.html). You can issue `celery inspect active_queues` to examine consumed queues.

## Execute unit tests

Make sure you have the requirements installed:
```sh
pip install -r backend/requirements.txt
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
- user: `node-1`
- pass: `p@sswr0d44`

Provided you have correctly setup your [network configuration](https://doc.substra.ai/setup/local_install_skaffold.html#network), you can use them to access the exposed API at http://substra-backend.node-1.com/

## Compatibility

Make sure you deploy this backend with a compatible ecosystem (chaincode, hlf-k8s, etc).
Always refer to the [compatibility table](https://github.com/SubstraFoundation/substra#compatibility-table).

The recommended way to run a specific version (0.1.6) of substra-backend is to execute:

```bash
SUBSTRA_BACKEND_VERSION=0.1.6
git checkout $SUBSTRA_BACKEND_VERSION
skaffold deploy --images substrafoundation/substra-backend:$SUBSTRA_BACKEND_VERSION
```

## Companion repositories

The Substra platform is built from several components (see the [architecture](https://doc.substra.ai/architecture.html) documentation for a comprehensive overview):

- [hlf-k8s](https://github.com/SubstraFoundation/hlf-k8s) is the implementation of Hyperledger Fabric on which this backend rely
- [orchestrator](https://github.com/owkin/orchestrator) contains the orchestration logic of a federated learning deployment
- [substra-frontend](https://github.com/SubstraFoundation/substra-frontend) is the frontend consuming the API exposed by the backend
- [substra-tests](https://github.com/SubstraFoundation/substra-tests) is the Substra end to end test suite

## License

This project is developed under the Apache License, Version 2.0 (Apache-2.0), located in the [LICENSE](./LICENSE) file.
