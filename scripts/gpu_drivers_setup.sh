#!/bin/env bash
#
# Setups GPU drivers for either Nvidia, AMD, or Intel
#

# Support for GPUs used when plotting/farming
if [[ ${OPENCL_GPU} == 'nvidia' ]]; then  
    mkdir -p /etc/OpenCL/vendors
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd
    echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf 
    echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf
    echo "Enabling Nvidia GPU support inside this container."
elif [[ ${OPENCL_GPU} == 'amd' ]]; then
    pushd /tmp > /dev/null
    echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
    apt-get update 2>&1 > /tmp/amdgpu_setup.log
    amdgpu-install -y --usecase=opencl --opencl=rocr --no-dkms --no-32 --accept-eula 2>&1 >> /tmp/amdgpu_setup.log
    popd > /dev/null
    echo "Enabling AMD GPU support inside this container."
elif [[ ${OPENCL_GPU} == 'intel' ]]; then
    apt-get update 2>&1 > /tmp/intelgpu_setup.log
    apt-get install -y intel-opencl-icd 2>&1 >> /tmp/intelgpu_setup.log
    echo "Enabling Intel GPU support inside this container."
fi
