#!/bin/bash

BASEDIR=$(dirname "$0")
# clean medias
rm -rf ${BASEDIR}/../medias/*

# copy medias orgs
cp -R ${BASEDIR}/../fixtures/chunantes ${BASEDIR}/../medias/
cp -R ${BASEDIR}/../fixtures/owkin ${BASEDIR}/../medias/
