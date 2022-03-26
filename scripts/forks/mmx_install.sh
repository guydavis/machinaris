#!/bin/env bash
#
# Installs MMX as per https://github.com/madMAx43v3r/mmx-node
#

MMX_BRANCH=$1
# On 2022-03-24
HASH=4ee2681e6d9882f4c16a6ba15d7c6af2c46d21f4

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
	#git checkout $HASH
	./make_devel.sh
fi
