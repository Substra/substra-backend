#!/bin/bash

dropdb substrabac_owkin
createdb -E UTF8 substrabac_owkin
psql -d substrabac_owkin -c "GRANT ALL PRIVILEGES ON DATABASE substrabac_owkin to substrabac;ALTER ROLE substrabac WITH SUPERUSER CREATEROLE CREATEDB;"

dropdb substrabac_chunantes
createdb -E UTF8 substrabac_chunantes
psql -d substrabac_chunantes -c "GRANT ALL PRIVILEGES ON DATABASE substrabac_chunantes to substrabac;ALTER ROLE substrabac WITH SUPERUSER CREATEROLE CREATEDB;"
