#!/bin/bash

# load dumps
BASEDIR=$(dirname "$0")
psql -d substrabac_chunantes < ${BASEDIR}/../fixtures/dump_substrabac_chunantes.sql
psql -d substrabac_owkin < ${BASEDIR}/../fixtures/dump_substrabac_owkin.sql
