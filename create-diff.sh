#!/bin/bash

CRATE=$1
INITIAL_VERSION=$2
FINAL_VERSION=$3

docker run \
  --rm \
  -it \
  -v ${PWD}:/cargo-diff \
  cargo-diff \
  --crate ${CRATE} --initial_version ${INITIAL_VERSION} --final_version ${FINAL_VERSION}
