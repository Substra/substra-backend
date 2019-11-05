#!/bin/bash

dropdb -U ${USER} backend
createdb -U ${USER} -E UTF8 backend
psql -U ${USER} -d backend -c "CREATE USER backend WITH PASSWORD 'backend' CREATEDB CREATEROLE SUPERUSER;"

dropdb -U ${USER} backend_owkin
createdb -U ${USER} -E UTF8 backend_owkin
psql -U ${USER} -d backend_owkin -c "GRANT ALL PRIVILEGES ON DATABASE backend_owkin to backend;ALTER ROLE backend WITH SUPERUSER CREATEROLE CREATEDB;"

dropdb -U ${USER} backend_chunantes
createdb -U ${USER} -E UTF8 backend_chunantes
psql -U ${USER} -d backend_chunantes -c "GRANT ALL PRIVILEGES ON DATABASE backend_chunantes to backend;ALTER ROLE backend WITH SUPERUSER CREATEROLE CREATEDB;"

dropdb -U ${USER} backend_clb
createdb -U ${USER} -E UTF8 backend_clb
psql -U ${USER} -d backend_clb -c "GRANT ALL PRIVILEGES ON DATABASE backend_chunantes to backend;ALTER ROLE backend WITH SUPERUSER CREATEROLE CREATEDB;"
