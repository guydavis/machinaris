#!/bin/bash
set -x
set -u
set -e
TAG=${TAG:-latest}
FORK=${FORK:-"*"}
IMAGE="${IMAGE:-"machinaris"}"

for file in scripts/forks/${FORK} ; do
	. "${file}"

	# collect build-args parameters
	build_args=""
	for line in $(awk '/^[A-Z].*/' $file); do
		build_args="$build_args --build-arg $line"
	done

	echo "Building Image for Chia-Fork ${CHIA_FORK}..."
	docker build --no-cache -t ${IMAGE}-${CHIA_FORK}:${TAG} -f docker/dockerfile ${build_args} .
  docker push ${IMAGE}-${CHIA_FORK}:${TAG}
done
