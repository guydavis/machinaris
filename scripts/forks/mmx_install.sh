#!/bin/env bash
#
# Installs MMX as per https://github.com/madMAx43v3r/mmx-node
#

MMX_BRANCH=$1
# On 2021-12-29 - temporarily disable as no releases are happening
#HASH=00fdc419a6b5d9ad7c00839dbf9af93014673a18

if [ -z ${MMX_BRANCH} ]; then
	echo 'Skipping MMX install as not requested.'
else
	rm -rf /root/.cache
	apt-get update
	apt-get install -y git cmake build-essential libsecp256k1-dev libsodium-dev zlib1g-dev ocl-icd-opencl-dev clinfo screen librocksdb-dev
	git clone --branch ${MMX_BRANCH} --single-branch https://github.com/madMAx43v3r/mmx-node.git /mmx-node
	cd /mmx-node
	git submodule update --init --recursive 
	#git checkout $HASH
	./make_devel.sh
fi
