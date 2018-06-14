#!/bin/bash

# get os
export ARCH=$(echo "$(uname -s|tr '[:upper:]' '[:lower:]'|sed 's/mingw64_nt.*/windows/')-$(uname -m | sed 's/x86_64/amd64/g')" | awk '{print tolower($0)}')

echo $ARCH
# get binaries
curl https://nexus.hyperledger.org/content/repositories/releases/org/hyperledger/fabric/hyperledger-fabric/${ARCH}-1.1.0/hyperledger-fabric-${ARCH}-1.1.0.tar.gz | tar xz

# remove config directory
rm -r config