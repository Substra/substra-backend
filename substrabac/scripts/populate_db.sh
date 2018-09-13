#!/bin/bash

# load dumps
BASEDIR=$(dirname "$0")
psql -U ${USER} -d substrabac_chunantes < ${BASEDIR}/../fixtures/dump_substrabac_chunantes.sql
psql -U ${USER} -d substrabac_owkin < ${BASEDIR}/../fixtures/dump_substrabac_owkin.sql
