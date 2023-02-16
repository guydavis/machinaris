#!/bin/env bash
#
# Installs Gigahorse as per https://github.com/madMAx43v3r/chia-gigahorse
#

GIGAHORSE_BRANCH=$1
GIGAHORSE_VERSION=${GIGAHORSE_BRANCH#?}  # Strip off the leading 'v' from his branch

if [ -z ${GIGAHORSE_BRANCH} ]; then
    echo 'Skipping Gigahorse install as not requested.'
else
    cd /tmp
    rm -rf /root/.cache
	apt-get update && apt-get install -y dialog apt-utils libgomp1
	# Install dependencies for GPU support
	apt-get install -y git cmake build-essential ocl-icd-opencl-dev clinfo screen initramfs-tools ocl-icd-libopencl1 opencl-headers libnuma1
	# For AMDGPU, install the amdgpu-install stub, optionally invoked later if OPENCL_GPU=amd at launch time
	curl -O http://repo.radeon.com/amdgpu-install/22.20.5/ubuntu/jammy/amdgpu-install_22.20.50205-1_all.deb
	apt-get install -y ./amdgpu-install_22.20.50205-1_all.deb
	
    arch_name="$(uname -m)"
    url="https://github.com/madMAx43v3r/chia-gigahorse/releases/download/${GIGAHORSE_BRANCH}/chia-gigahorse-farmer-${GIGAHORSE_VERSION}-${arch_name}.tar.gz"
    echo "Pulling Madmax closed-source Chia farming binary from..."
    echo ${url}
    cd / && curl --retry 5 --retry-max-time 120 -skJLO ${url}
    du -hsc chia-gigahorse-farmer*
    tar -xzf chia-gigahorse-farmer*
fi
