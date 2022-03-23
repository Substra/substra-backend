# How-to run API locally

Steps to run django server in a virtualenv, without needing a k8s cluster.

## Define settings

```sh
export DJANGO_SETTINGS_MODULE=backend.settings.localdev
```

## Start the DB

### Option 1: using a container

```
make db
```

### Option 2: using native install

Documented for macOS.

#### Server

You can use [edb bundle](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) (version >= 11). This comes with pgAdmin 4.

#### Client (psql)

```sh
brew install postgres
```

#### Database

Create a `substra` database.

```sh
psql postgresql://postgres:postgres@localhost:5432/postgres -c "CREATE DATABASE substra;"
```

Note: to use another DB name, set the `BACKEND_DB_NAME` env var.

## Load data

### Option 1: restore a dump

```sh
cat dump-file.sql | docker exec -it postgres psql postgresql://postgres:postgres@localhost:5432/substra
```

### Option 2: create data

Replace `user` and `password` by values of your choice.

```sh
python backend/manage.py migrate
python backend/manage.py add_user <user> <password> mychannel
python backend/manage.py generate_fixtures
```

## Start the API

For now only isolated mode is supported: without assert registration or task computation.

```sh
ISOLATED=1 python backend/manage.py runserver
```

## Connect clients

### Frontend

```sh
export API_URL=http://127.0.0.1:8000
```

### Substra

```sh
substra config --profile localdev http://127.0.0.1:8000
```
