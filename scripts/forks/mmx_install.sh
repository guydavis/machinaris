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
	# Install dependencies
	apt-get install -y git cmake build-essential libsecp256k1-dev librocksdb-dev libsodium-dev zlib1g-dev ocl-icd-opencl-dev clinfo screen initramfs-tools ocl-icd-libopencl1 opencl-headers apt-utils libnuma1
	# For AMDGPU, install the amdgpu-install stub, optionally invoked later if OPENCL_GPU=amd at launch time
	curl -O http://repo.radeon.com/amdgpu-install/21.40.2/ubuntu/focal/amdgpu-install_21.40.2.40502-1_all.deb
	apt install -y ./amdgpu-install_21.40.2.40502-1_all.deb
	# Clone and install MMX
	git clone --branch ${MMX_BRANCH} --single-branch https://github.com/madMAx43v3r/mmx-node.git /mmx-node
	cd /mmx-node
	git submodule update --init --recursive 
	#git checkout $HASH
	./make_devel.sh
fi
