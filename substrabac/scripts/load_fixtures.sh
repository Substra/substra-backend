#!/bin/bash

# load dumps
# TODO use django fixtures
BASEDIR=$(dirname "$0")
echo "$BASEDIR"
psql -d substrabac_chunantes < ${BASEDIR}/../fixtures/dump_substrabac_chunantes.sql
psql -d substrabac_owkin < ${BASEDIR}/../fixtures/dump_substrabac_owkin.sql

# clean medias
rm -rf ${BASEDIR}/../medias/*

# copy medias orgs
cp -R ${BASEDIR}/../fixtures/chunantes ${BASEDIR}/../medias/
cp -R ${BASEDIR}/../fixtures/owkin ${BASEDIR}/../medias/