#!/bin/bash

GUPPY_OUTPUT=$1

docker run \
  --rm \
  -it \
  -v ${PWD}:/cargo-diff \
  cargo-diff \
  --guppy ${GUPPY_OUTPUT}
