#!/bin/env bash
#
# Installs MMX as per https://github.com/madMAx43v3r/mmx-node
#

MMX_BRANCH=$1
# On 2022-06-02
HASH=f8ea5be1b2fb61160898d0164cad152da25f4c45

if [ -z ${MMX_BRANCH} ]; then
	echo 'Skipping MMX install as not requested.'
else
	rm -rf /root/.cache
	apt-get update
	# Install dependencies
	apt-get install -y git cmake build-essential libsecp256k1-dev librocksdb-dev libsodium-dev zlib1g-dev ocl-icd-opencl-dev clinfo screen initramfs-tools ocl-icd-libopencl1 opencl-headers apt-utils libnuma1
	# For AMDGPU, install the amdgpu-install stub, optionally invoked later if OPENCL_GPU=amd at launch time
	curl -O http://repo.radeon.com/amdgpu-install/21.40/ubuntu/focal/amdgpu-install-21.40.40500-1_all.deb
	apt install -y ./amdgpu-install-21.40.40500-1_all.deb
	# Clone and install MMX
	git clone --branch ${MMX_BRANCH} --single-branch https://github.com/madMAx43v3r/mmx-node.git /mmx-node
	cd /mmx-node
	git submodule update --init --recursive 
	git checkout $HASH
	./make_release.sh
fi
