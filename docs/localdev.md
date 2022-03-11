
## Howto run substrapp locally
Here is an example of workflow to develop API, and/or to develop frontend:

### Prerequisite:
- Install `psql`: `brew install postgres`
- Have a dump file for substra db: For example, `substra-prod01-20220311.sql.gz` accessible in [this drive](https://drive.google.com/drive/u/0/folders/1i15shc7Yk_V1LxdZQJ12K6EV0m02F_8P). (Note this dump is compatible with backend version `test-localrep-9`)

### Three steps to run
1/ run `make db-test` -> This will run a docker embedding a postgres server with a db named substra, and with port forwarded to 5432

2/ Populate it with data
- If you have a substra db dump file, restore it: `(zcat < substra-mdy-prod-20220223-0759.sql.gz) | psql postgresql://postgres:postgres@localhost:5432/substra`

3/ In a venv with backend requirements installed, run django app with localdev settings, in isolated mode, and targeting our new db: `DJANGO_SETTINGS_MODULE=backend.settings.localdev ISOLATED=1 python backend/manage.py runserver`

And now enjoy having a substra backend served in seconds, without needing a k8s cluster, nor an orchestrator. Off course you will not have a full-featured connect instance (no task computation engine, no asset registration, etc).

/!\ Please note that the server will be served on localhost at port 8000 (80 is the dedicated http port for prod). Clients should adapt accordingly (ex: via `API_URL` var for frontend)

### Alternative to make db-test: With a native postgres install
Instead of running postgres in a docker, you may use your native postgres.

Postgres install:
- A good option to install postgres on MacOs is to use [edb bundle](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) (version >= 11). This comes with pgAdmin 4.
- Install should then be completed with `brew install postgres` in order to have `psql`.

Database creation:
- It can be done via pgAdming4 or via a psql command `psql postgresql://postgres:postgres@localhost:5432/postgres -c "CREATE DATABASE substra"`
- Note: If you use a db with another name, you need to tell django with `BACKEND_DB_NAME` env var. Ex: `DJANGO_SETTINGS_MODULE=backend.settings.localdev ISOLATED=1 BACKEND_DB_NAME=my_db python backend/manage.py runserver`
