#!/bin/bash

CRATE=$1
VERSION=$2

docker run \
  --rm \
  -it \
  -v ${PWD}:/cargo-diff \
  cargo-diff \
  --crate ${CRATE} --version ${VERSION}
