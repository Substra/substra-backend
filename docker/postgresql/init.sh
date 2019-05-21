#!/bin/bash

createdb -U ${USER} -E UTF8 substrabac_owkin
psql -U ${USER} -d substrabac_owkin -c "GRANT ALL PRIVILEGES ON DATABASE substrabac_owkin to substrabac;ALTER ROLE substrabac WITH SUPERUSER CREATEROLE CREATEDB;"

createdb -U ${USER} -E UTF8 substrabac_chunantes
psql -U ${USER} -d substrabac_chunantes -c "GRANT ALL PRIVILEGES ON DATABASE substrabac_chunantes to substrabac;ALTER ROLE substrabac WITH SUPERUSER CREATEROLE CREATEDB;"


createdb -U ${USER} -E UTF8 substrabac_clb
psql -U ${USER} -d substrabac_clb -c "GRANT ALL PRIVILEGES ON DATABASE substrabac_clb to substrabac;ALTER ROLE substrabac WITH SUPERUSER CREATEROLE CREATEDB;"
