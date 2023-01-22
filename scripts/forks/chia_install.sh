#!/bin/env bash
#
# Installs Chia as per https://github.com/Chia-Network/chia-blockchain
#

CHIA_BRANCH=$1

if [ -z ${CHIA_BRANCH} ]; then
    echo 'Skipping Chia install as not requested.'
else
    cd /tmp
    rm -rf /root/.cache
	apt-get update && apt-get install -y dialog apt-utils
	# Install dependencies for GPU support
	apt-get install -y git cmake build-essential ocl-icd-opencl-dev clinfo screen initramfs-tools ocl-icd-libopencl1 opencl-headers
	# For AMDGPU, install the amdgpu-install stub, optionally invoked later if OPENCL_GPU=amd at launch time
	curl -O http://repo.radeon.com/amdgpu-install/22.20.5/ubuntu/jammy/amdgpu-install_22.20.50205-1_all.deb
	apt-get install -y ./amdgpu-install_22.20.50205-1_all.deb
	
    git clone --branch ${CHIA_BRANCH} --recurse-submodules=mozilla-ca https://github.com/Chia-Network/chia-blockchain.git /chia-blockchain
    cd /chia-blockchain

    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' chia/wallet/wallet_state_manager.py

	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py

    /bin/sh ./install.sh
fi
