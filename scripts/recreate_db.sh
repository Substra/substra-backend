#!/bin/bash

dropdb -U ${USER} substrabac
createdb -U ${USER} -E UTF8 substrabac
psql -U ${USER} -d substrabac -c "CREATE USER substrabac WITH PASSWORD 'substrabac' CREATEDB CREATEROLE SUPERUSER;"

dropdb -U ${USER} substrabac_owkin
createdb -U ${USER} -E UTF8 substrabac_owkin
psql -U ${USER} -d substrabac_owkin -c "GRANT ALL PRIVILEGES ON DATABASE substrabac_owkin to substrabac;ALTER ROLE substrabac WITH SUPERUSER CREATEROLE CREATEDB;"

dropdb -U ${USER} substrabac_chunantes
createdb -U ${USER} -E UTF8 substrabac_chunantes
psql -U ${USER} -d substrabac_chunantes -c "GRANT ALL PRIVILEGES ON DATABASE substrabac_chunantes to substrabac;ALTER ROLE substrabac WITH SUPERUSER CREATEROLE CREATEDB;"

dropdb -U ${USER} substrabac_clb
createdb -U ${USER} -E UTF8 substrabac_clb
psql -U ${USER} -d substrabac_clb -c "GRANT ALL PRIVILEGES ON DATABASE substrabac_chunantes to substrabac;ALTER ROLE substrabac WITH SUPERUSER CREATEROLE CREATEDB;"
