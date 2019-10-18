#!/bin/bash

# load dumps
BASEDIR=$(dirname "$0")
psql -U ${USER} -d substrabackend_chunantes < ${BASEDIR}/../fixtures/dump_substrabackend_chunantes.sql
psql -U ${USER} -d substrabackend_owkin < ${BASEDIR}/../fixtures/dump_substrabackend_owkin.sql
