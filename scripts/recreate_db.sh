#!/bin/bash

dropdb -U ${USER} substrabackend
createdb -U ${USER} -E UTF8 substrabackend
psql -U ${USER} -d substrabackend -c "CREATE USER substrabackend WITH PASSWORD 'substrabackend' CREATEDB CREATEROLE SUPERUSER;"

dropdb -U ${USER} substrabackend_owkin
createdb -U ${USER} -E UTF8 substrabackend_owkin
psql -U ${USER} -d substrabackend_owkin -c "GRANT ALL PRIVILEGES ON DATABASE substrabackend_owkin to substrabackend;ALTER ROLE substrabackend WITH SUPERUSER CREATEROLE CREATEDB;"

dropdb -U ${USER} substrabackend_chunantes
createdb -U ${USER} -E UTF8 substrabackend_chunantes
psql -U ${USER} -d substrabackend_chunantes -c "GRANT ALL PRIVILEGES ON DATABASE substrabackend_chunantes to substrabackend;ALTER ROLE substrabackend WITH SUPERUSER CREATEROLE CREATEDB;"

dropdb -U ${USER} substrabackend_clb
createdb -U ${USER} -E UTF8 substrabackend_clb
psql -U ${USER} -d substrabackend_clb -c "GRANT ALL PRIVILEGES ON DATABASE substrabackend_chunantes to substrabackend;ALTER ROLE substrabackend WITH SUPERUSER CREATEROLE CREATEDB;"
