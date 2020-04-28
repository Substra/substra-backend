# Substra-Backend [![Build Status](https://travis-ci.org/SubstraFoundation/substra-backend.svg?branch=master)](https://travis-ci.org/SubstraFoundation/substra-backend)

Backend of the Substra platform

|  substra-backend | celeryworker | celerybeat | flower |
| ------------- | ------------- | ------------- | ------------- |
| [![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/substrafoundation/substra-backend)](https://hub.docker.com/r/substrafoundation/substra-backend/builds) | [![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/substrafoundation/celeryworker)](https://hub.docker.com/r/substrafoundation/celeryworker/builds) | [![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/substrafoundation/celerybeat)](https://hub.docker.com/r/substrafoundation/celerybeat/builds) | [![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/substrafoundation/flower)](https://hub.docker.com/r/substrafoundation/flower/builds) |

## Version

You will note substra-backend use a versioned REST API with the header protocol.
Current is `0.0`.

## Getting started 1: Prepare the django app

1. Clone the repo:
 ```
 git clone https://github.com/SubstraFoundation/substra-backend
 ```
2. If you are on Linux, follow the [Linux user namespaces instructions](./doc/linux-userns-guide.md)
3. Install dependencies (might be useful to create a virtual environment before, eg using virtualenv and virtualenvwrapper):
  - For numpy, scipy, and pandas (for Ubuntu & Debian users): `sudo apt-get install python-numpy python-scipy python-pandas`
  - `pip install -r requirements.txt`
4. Setup the database:
  - Install [PostgreSQL](https://www.postgresql.org/download/) if needed
  - [Create a database](https://www.postgresql.org/docs/10/static/tutorial-createdb.html).
5. Create a main postgresql use with password:
  ```shell
  $> sudo su postgres
  $> psql
  $ CREATE USER backend WITH PASSWORD 'backend' CREATEDB CREATEROLE SUPERUSER;
  ```
6. Create two databases for both orgs: owkin and chu-nantes. A shell script is available, do not hesitate to run it.
It will drop the databases if they are already created, then create them and grant all privileges to your main user backend.
 (If this is the first time you create the databases, you will see some warnings which are pointless):

  ```shell
  $> ./scripts/recreate_db.sh
```
7. We will populate data:

###### Clean environment (recommanded)

- With django migrations
```shell
BACKEND_ORG=owkin BACKEND_DEFAULT_PORT=8000 python backend/manage.py migrate --settings=backend.settings.dev
BACKEND_ORG=chu-nantes BACKEND_DEFAULT_PORT=8001 python backend/manage.py migrate --settings=backend.settings.dev
```

###### With fixtures (fixtures container has been run from hlf-k8s, old behavior for testing)

data in fixtures are relative to the data already set in the ledger if the fixtures container instance succeeded

Two solutions:
- With django migrations + load data
```shell
BACKEND_ORG=owkin BACKEND_DEFAULT_PORT=8000 python backend/manage.py migrate --settings=backend.settings.dev
BACKEND_ORG=chu-nantes BACKEND_DEFAULT_PORT=8001 python backend/manage.py migrate --settings=backend.settings.dev
BACKEND_ORG=owkin BACKEND_DEFAULT_PORT=8000 python backend/manage.py loaddata ./fixtures/data_owkin.json --settings=backend.settings.dev
BACKEND_ORG=chu-nantes BACKEND_DEFAULT_PORT=8001 python backend/manage.py loaddata ./fixtures/data_chu-nantes.json --settings=backend.settings.dev
```
- From dumps:
```shell
  $> ./scripts/populate_db.sh
```
If you don't want to replicate the data in the ledger, simply run the django migrations.

Populate media files
```shell
  $> ./scripts/load_fixtures.sh
```
It will clean the `medias` folders and create the `owkin` and `chu-nantes` folders in the `medias` folder.


8. Optional: Create a superuser in your databases:
```shell
BACKEND_ORG=owkin BACKEND_DEFAULT_PORT=8000 ./backend/manage.py createsuperuser --settings=backend.settings.dev
BACKEND_ORG=chu-nantes BACKEND_DEFAULT_PORT=8001 ./backend/manage.py createsuperuser --settings=backend.settings.dev
```

## Getting started 2: Linking the app with Hyperledger Fabric


### Make the hlf-k8s available to the app

[See here](https://github.com/SubstraFoundation/hlf-k8s#network).

### Install rabbitmq

```shell
sudo apt-get install rabbitmq-server
```

### Launch celery workers/scheduler and celery beat

Execute this command in the `backend/backend` folder.

Note the use of the development settings.

```shell
DJANGO_SETTINGS_MODULE=backend.settings.dev BACKEND_ORG=owkin BACKEND_DEFAULT_PORT=8000 BACKEND_PEER_PORT_EXTERNAL=9051 celery -E -A backend worker -l info -B -n owkin -Q owkin,scheduler,celery --hostname owkin.scheduler
DJANGO_SETTINGS_MODULE=backend.settings.dev BACKEND_ORG=owkin BACKEND_DEFAULT_PORT=8000 BACKEND_PEER_PORT_EXTERNAL=9051 celery -E -A backend worker -l info -B -n owkin -Q owkin,owkin.worker,celery --hostname owkin.worker
DJANGO_SETTINGS_MODULE=backend.settings.dev BACKEND_ORG=chu-nantes BACKEND_DEFAULT_PORT=8001 BACKEND_PEER_PORT_EXTERNAL=7051 celery -E -A backend worker -l info -B -n chunantes -Q chu-nantes,scheduler,celery --hostname chu-nantes.scheduler
DJANGO_SETTINGS_MODULE=backend.settings.dev BACKEND_ORG=chu-nantes BACKEND_DEFAULT_PORT=8001 BACKEND_PEER_PORT_EXTERNAL=7051 celery -E -A backend worker -l info -B -n chunantes -Q chu-nantes,chu-nantes.worker,celery --hostname chu-nantes.worker
DJANGO_SETTINGS_MODULE=backend.settings.common celery -A backend beat -l info
```

## Launch the servers

Go in the `backend` folder and run the server locally:
:warning: <p style="color: red">Be very careful, --settings is different here, `server` is needed.</p>

```shell
BACKEND_ORG=owkin BACKEND_DEFAULT_PORT=8000 BACKEND_PEER_PORT_EXTERNAL=9051 ./manage.py runserver 8000 --settings=backend.settings.server.dev
BACKEND_ORG=chu-nantes BACKEND_DEFAULT_PORT=8001 BACKEND_PEER_PORT_EXTERNAL=7051 ./manage.py runserver 8001 --settings=backend.settings.server.dev
```

## Generate nodes authentication

For working with node to node authentication, you need to generate and then load some fixtures
```shell
python ./backend/node/generate_nodes.py
BACKEND_ORG=owkin BACKEND_DEFAULT_PORT=8000 ./manage.py init_nodes ./backend/node/nodes/owkinMSP.json --settings=backend.settings.dev
BACKEND_ORG=chu-nantes BACKEND_DEFAULT_PORT=8001 ./manage.py init_nodes ./backend/node/nodes/chu-nantesMSP.json --settings=backend.settings.dev
```

## Create a default user

A django admin command is available for registering a user:
```shell
./manage.py add_user $USERNAME $PASSWORD
```

The populate.py file will use for each organization credentials `substra/p@$swr0d44` for connection.
Create these users with:

```shell
BACKEND_ORG=owkin ./backend/manage.py add_user substra 'p@$swr0d44' --settings=backend.settings.dev
BACKEND_ORG=chu-nantes ./backend/manage.py add_user substra 'p@$swr0d44' --settings=backend.settings.dev
```

## Test with unit and functional tests

```shell
    make test
    make coverage  # For shell report
    coverage html  # For HTML report
```

## Test by creating a traintuple

###### Clean environment

Run the `populate.py` script which will create data in the ledger with a traintuple.
Check the status of the created traintuple `http://localhost:8000/traintuple/`
If everything run correctly, its status should pas from `todo->train->trained->testing->tested->done`.

When you want to re-run the testing process:
- Close every connections to the databases.
- Stop all your services and containers.
- Rerun `recreate_db.sh` and `clean_media.sh` scripts.
- Run the django migrations.
- Relaunch your hlf-k8s network.
- Run the owkin and chunantes substra-backend servers.
- Run celery beat and celery owkin and chu-nantes.
- Run the `populate.py` python script.

###### With fixtures

You can test your environment by creating a traintuple:
```shell
curl -H "Accept: text/html;version=0.0, */*;version=0.0" -H "Content-Type: application/json" -d '{"algo_key":"da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b","model_key":"","train_data_sample_keys":["62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a","42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"]}' -X POST http://localhost:8001/traintuple/?format=json
```
It will try to create a traintuple with creator: chu-nantes (localhost:8001).
The chu-nantes celery worker will try to add the traintuple to the ledger.
You can check your traintuple has been corectly added by visiting `http://localhost:8000/traintuple/` or `http://localhost:8001/traintuple/`
As the trainDataSample passed are also created by chu-nantes, the chu-nantes celery worker will try to update the traintuple status to `training` and save some data if needed.
You can check `http://localhost:8000/traintuple/` or `http://localhost:8001/traintuple/` to check if the status of your newly created traintuple is set to `training` after 10 sec (celery worker periodic task period).
You can also check a new objective has been added in `medias/chu-nantes` with a `metrics.py` file but not `description.md` file.

## Launching with docker

As for hlf-k8s, you can launch all the services in docker containers.

First, Make sure you've generated some nodes artifacts:
```bash
$> python ./backend/node/generate_nodes.py
```

Then, build the images:
```bash
$> sh build-docker-images.sh
```

Then, go to the `docker` dir and run `start.py` (`-d` means `dev` settings):
```bash
$> python start.py -d --no-backup
```

Check your services are correctly started with `docker ps -a`.

## Expiry token period

Two global environment variables `ACCESS_TOKEN_LIFETIME` and `EXPIRY_TOKEN_LIFETIME` expressed in minutes can be set for dealing with expiry token period.
The first one `ACCESS_TOKEN_LIFETIME` deals with JWT Authentication.
THe second one `EXPIRY_TOKEN_LIFETIME` deals with simple token expiration.
By default, set to 24*60 min i.e 24h.

## Testing fabric-sdk-py

A directory named `fabric-sdk-py_tests` is available to the root of this project.
If you launch a hlf-k8s setup, you will be able to play with theses tests.
For `fabric-sdk-py-query-invoke.py`, be sure to have run the `generateNetworkFile.py` script for producing the network.json file needed.

## Miscellaneous

- [PyCharm setup](./doc/pycharm-setup.md)

## License

This project is developed under the Apache License, Version 2.0 (Apache-2.0), located in the [LICENSE](./LICENSE) file.
