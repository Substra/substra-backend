# How-to run API locally

Steps to run django server in a virtualenv, without needing a k8s cluster.
For now only isolated mode is supported: without assert registration or task computation.

## Quickstart

Activate a virtualenv, then run the commands:

```sh
make db  # start postgres instance inside a container named `postgres`
make install  # install python dependencies
make quickstart  # run migrations, create a user, generate assets fixtures, start the server
```

Connect substra client (`node-1` profile is used by Titanic example).

```sh
substra config --profile node-1 http://127.0.0.1:8000
substra login --profile node-1 -u node-1 -p p@sswr0d44
substra list --profile node-1 algo  # should display fixtures
```

## (Optional) Restore a dump

Warning: it will erase the database content (user, fixtures, etc).

```sh
cat dump-file.sql | docker exec -it postgres psql postgresql://postgres:postgres@localhost:5432/substra
```

## (Optional) Use another DB

### Install postgres on macOS

You can use [edb bundle](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) (version >= 11). This comes with pgAdmin 4.

```sh
brew install postgres  # install the psql client
```

### Create a database

Create a `substra` database. To use another name, set the `BACKEND_DB_NAME` env var accordingly.

```sh
psql postgresql://postgres:postgres@localhost:5432/postgres -c "CREATE DATABASE substra;"
```
