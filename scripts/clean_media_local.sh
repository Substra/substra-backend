#!/bin/bash

BASEDIR="$(dirname $(dirname $0))"

echo $BASEDIR
# clean medias
rm -rf ${BASEDIR}/backend/medias/*
