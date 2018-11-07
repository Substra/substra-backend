#!/bin/bash

BASEDIR=$(dirname "$0")

createCustomDockerImages() {
    for dir in $BASEDIR/docker/*/; do
        dir=`basename $dir`
        docker build -t substra/$dir -f $BASEDIR/docker/$dir/Dockerfile .
    done
}

echo "===> Create custom docker images"
createCustomDockerImages
