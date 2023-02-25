#!/bin/export bash
#
# Installs GPU drivers for both AMD and Nvidia
#

arch_name="$(uname -m)"
ubuntu_ver=`lsb_release -r -s`
echo "Installing GPU drivers on ${arch_name} for ${ubuntu_ver}..."

# Install dependencies for GPU support of OpenCL
apt update && apt install -y git cmake build-essential ocl-icd-opencl-dev clinfo screen initramfs-tools ocl-icd-libopencl1 opencl-headers libnuma1

# For AMDGPU, install the amdgpu-install stub, optionally invoked later if OPENCL_GPU=amd at launch time
amd_deb=$(curl -s http://repo.radeon.com/amdgpu-install/latest/ubuntu/jammy/ | grep -m 1 -Po "amdgpu-install_[-\.\d]+_all.deb" | head -1)
curl -O http://repo.radeon.com/amdgpu-install/latest/ubuntu/jammy/${amd_deb}
apt install -y ./${amd_deb}

# For Nvidia, install drivers as per https://gitlab.com/nvidia/container-images/cuda/-/blob/master/dist/11.5.0/ubuntu2004/base/Dockerfile
if [[ "${arch_name}" = "x86_64" ]]; then
tee -a /etc/profile <<EOF
export NVARCH='x86_64'
export NVIDIA_REQUIRE_CUDA='cuda>=11.5 brand=tesla,driver>=418,driver<419 brand=tesla,driver>=450,driver<451 brand=tesla,driver>=470,driver<471 brand=unknown,driver>=470,driver<471 brand=nvidia,driver>=470,driver<471 brand=nvidiartx,driver>=470,driver<471 brand=geforce,driver>=470,driver<471 brand=geforcertx,driver>=470,driver<471 brand=quadro,driver>=470,driver<471 brand=quadrortx,driver>=470,driver<471 brand=titan,driver>=470,driver<471 brand=titanrtx,driver>=470,driver<471'
export NV_CUDA_CUDART_VERSION='11.5.50-1'
export NV_CUDA_COMPAT_PACKAGE='cuda-compat-11-5'
export CUDA_VERSION='11.5.0'
EOF
elif [[ "${arch_name}" = "aarch64" ]]; then
tee -a /etc/profile <<EOF
export NVARCH='sbsa'
export NVIDIA_REQUIRE_CUDA='cuda>=11.5'
export NV_CUDA_CUDART_VERSION='11.5.50-1'
export CUDA_VERSION='11.5.0'
EOF
fi
source /etc/profile

# Install the correct Nvidia driver
apt install -y --no-install-recommends gnupg2 curl ca-certificates && \
    curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/${NVARCH}/3bf863cc.pub | apt-key add - && \
    echo "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/${NVARCH} /" > /etc/apt/sources.list.d/cuda.list

# For libraries in the cuda-compat-* package: https://docs.nvidia.com/cuda/eula/index.html#attachment-a
apt install -y --no-install-recommends cuda-cudart-11-5=${NV_CUDA_CUDART_VERSION} ${NV_CUDA_COMPAT_PACKAGE}
