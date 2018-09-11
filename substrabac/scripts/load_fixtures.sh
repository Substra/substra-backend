#!/bin/bash

BASEDIR=$(dirname "$0")
# clean medias
rm -rf ${BASEDIR}/../medias/*

# copy medias orgs
rsync --recursive ${BASEDIR}/../fixtures/chunantes ${BASEDIR}/../medias/
rsync --recursive ${BASEDIR}/../fixtures/owkin ${BASEDIR}/../medias/
