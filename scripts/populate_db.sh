#!/bin/bash

# load dumps
BASEDIR=$(dirname "$0")
psql -U ${USER} -d backend_chunantes < ${BASEDIR}/../fixtures/dump_backend_chunantes.sql
psql -U ${USER} -d backend_owkin < ${BASEDIR}/../fixtures/dump_backend_owkin.sql
