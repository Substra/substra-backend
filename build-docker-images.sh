#!/bin/bash

BASEDIR=$(dirname "$0")

createCustomDockerImages() {
    for dir in $BASEDIR/docker/*/; do
        dir=`basename $dir`
        DOCKERFILE=$BASEDIR/docker/$dir/Dockerfile

        if [ -f $DOCKERFILE ]; then
            docker build -t substra/$dir -f $DOCKERFILE .
        fi
    done
}

echo "===> Create custom docker images"
createCustomDockerImages
