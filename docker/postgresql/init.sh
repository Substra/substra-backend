#!/bin/bash

createdb -U ${USER} -E UTF8 substrabackend_owkin
psql -U ${USER} -d substrabackend_owkin -c "GRANT ALL PRIVILEGES ON DATABASE substrabackend_owkin to substrabackend;ALTER ROLE substrabackend WITH SUPERUSER CREATEROLE CREATEDB;"

createdb -U ${USER} -E UTF8 substrabackend_chunantes
psql -U ${USER} -d substrabackend_chunantes -c "GRANT ALL PRIVILEGES ON DATABASE substrabackend_chunantes to substrabackend;ALTER ROLE substrabackend WITH SUPERUSER CREATEROLE CREATEDB;"


createdb -U ${USER} -E UTF8 substrabackend_clb
psql -U ${USER} -d substrabackend_clb -c "GRANT ALL PRIVILEGES ON DATABASE substrabackend_clb to substrabackend;ALTER ROLE substrabackend WITH SUPERUSER CREATEROLE CREATEDB;"
