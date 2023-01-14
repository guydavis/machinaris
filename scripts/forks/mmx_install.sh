#!/bin/env bash
#
# Installs MMX as per https://github.com/madMAx43v3r/mmx-node
# using his binaries from https://github.com/madMAx43v3r/mmx-binaries.git
#

MMX_BRANCH=$1

if [ -z ${MMX_BRANCH} ]; then
	echo 'Skipping MMX install as not requested.'
else
	rm -rf /root/.cache
	apt-get update
	# Install dependencies for MMX and GPU support
	apt-get install -y git cmake build-essential libsecp256k1-dev libsodium-dev libminiupnpc-dev libjemalloc-dev zlib1g-dev ocl-icd-opencl-dev clinfo screen
	apt-get install -y initramfs-tools ocl-icd-libopencl1 opencl-headers apt-utils libnuma1
	# For AMDGPU, install the amdgpu-install stub, optionally invoked later if OPENCL_GPU=amd at launch time
	curl -O http://repo.radeon.com/amdgpu-install/22.20.5/ubuntu/jammy/amdgpu-install_22.20.50205-1_all.deb
	apt-get install -y ./amdgpu-install_22.20.50205-1_all.deb
	# Clone and install MMX from the author's own binaries, not linked to his code branches unfortunately
	pushd /tmp
	git clone --depth 1 --filter=blob:none --sparse https://github.com/madMAx43v3r/mmx-binaries.git
	pushd mmx-binaries/
	git sparse-checkout set mmx-node/linux/x86_64/
	pushd mmx-node/linux
	mv x86_64 /mmx-node
	popd
	rm -f mmx-binaries
	popd
fi
