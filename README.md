# Substra-Backend [![Build Status](https://travis-ci.org/SubstraFoundation/substra-backend.svg?branch=master)](https://travis-ci.org/SubstraFoundation/substra-backend) [![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/substrafoundation/substra-backend)](https://hub.docker.com/r/substrafoundation/substra-backend/builds)

Backend of the Substra platform

## Running a development instance

For the local installation of substra-backend (and companions), please refer to the [setup documentation](https://doc.substra.ai/setup/local_install_skaffold.html).

With [hlf-k8s]() already running and requirements fulfilled, this should boils down to:
```sh
skaffold dev
```

## Django management

To get access to the Django management tool, spawn a shell in the running container:
```sh
kubectl -n org-1 exec -i -t $(kubectl -n org-1 get pods -l=app.kubernetes.io/name=substra-backend-server -o name) -c substra-backend -- /bin/bash
```

This will also gives you access to the celery CLI.

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

## Accessing the app

On deployment, several user accounts are created (for [./values/backend-org-1.yaml](org1) and [./values/backend-org-2.yaml](org2)).

The sample credentials for org1 are:
- user: `node-1`
- pass: `p@$swr0d44`

You can use them to access the exposed API at http://substra-backend.node-1.com/

## Compatibility

Make sure you deploy this backend with a compatible ecosystem (chaincode, hlf-k8s, etc).
Always refer to the [compatibility table](https://github.com/SubstraFoundation/substra#compatibility-table).

## Miscellaneous

- [substra-tests](https://github.com/SubstraFoundation/substra-tests) is the Substra end to end test suite

## License

This project is developed under the Apache License, Version 2.0 (Apache-2.0), located in the [LICENSE](./LICENSE) file.
