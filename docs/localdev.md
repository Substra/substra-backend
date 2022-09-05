# How-to run API locally

Steps to run django server in a virtualenv, without needing a k8s cluster.
For now only isolated mode is supported: without assert registration or task computation.

## Quickstart

Start postgres instance

```sh
make db
```

Activate a virtualenv, then run the commands:

```sh
make install  # install python dependencies
make quickstart  # wait for db, run migrations, create a user, start the server
make fixtures  # generate assets fixtures
```

Alternatively, you can run it inside a container by using dev target (adapt to mount volumes you need).

```sh
docker build -f docker/substra-backend/Dockerfile --target dev -t substra-backend .
docker run -it --name substra-backend --rm -p 8000:8000 \
  -v ${PWD}/backend/substrapp:/usr/src/app/substrapp \
  -e DJANGO_SETTINGS_MODULE=backend.settings.localdev \
  -e ISOLATED=1 \
  -e BACKEND_DB_HOST=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' postgres) \
  substra-backend sh dev-startup.sh
docker exec substra-backend python manage.py generate_fixtures
```

Connect Substra client (`org-1` profile is used by Titanic example).

```sh
substra config --profile org-1 http://127.0.0.1:8000
substra login --profile org-1 -u org-1 -p p@sswr0d44
substra list --profile org-1 algo  # should display fixtures
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
