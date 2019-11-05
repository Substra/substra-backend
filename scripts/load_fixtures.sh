#!/bin/bash

BASEDIR="${SUBSTRA_PATH:-/substra}"
# clean medias
rm -rf ${BASEDIR}/medias/*

# copy medias orgs
rsync --recursive ${BASEDIR}/../fixtures/chunantes ${BASEDIR}/medias/
rsync --recursive ${BASEDIR}/../fixtures/owkin ${BASEDIR}/medias/

