#!/bin/env bash
#
# Installs bladebit - A fast Chia plotter, offering disk, ram, and gpu modes.
# See https://github.com/Chia-Network/bladebit
#

BLADEBIT_BRANCH=$1  # Now ignored as install binaries from Github.

if [[ (${mode} =~ ^fullnode.*  || ${mode} =~ "plotter") && (${blockchains} == 'chia') ]]; then
    if [ ! -f /usr/bin/bladebit ] && [[ "${bladebit_skip_build}" != 'true' ]]; then
        arch_name="$(uname -m)"
        apt update && apt install -y build-essential cmake libgmp-dev libnuma-dev
        cd / && echo "Installing bladebit on ${arch_name}..."

        # Now install CNI's separate binary for actual GPU plotting...
        mkdir -p /opt/chia/bladebit
        cd /opt/chia/bladebit
        rm -f ./bladebit*  # Remove any stale versions bundled in the DEB package.
        if [[ "${arch_name}" == "x86_64" ]]; then
            curl -sLJO https://github.com/Chia-Network/bladebit/releases/download/v3.1.0/bladebit-v3.1.0-ubuntu-x86-64.tar.gz
            curl -sLJO https://github.com/Chia-Network/bladebit/releases/download/v3.1.0/bladebit-cuda-v3.1.0-ubuntu-x86-64.tar.gz
        else
            curl -sLJO https://github.com/Chia-Network/bladebit/releases/download/v3.1.0/bladebit-v3.1.0-ubuntu-arm64.tar.gz
            curl -sLJO https://github.com/Chia-Network/bladebit/releases/download/v3.1.0/bladebit-cuda-v3.1.0-ubuntu-arm64.tar.gz
        fi
        tar -xvf bladebit-v3.*.tar.gz
        tar -xvf bladebit-cuda-v3.*.tar.gz
        rm -f *tar.gz
        chmod 755 bladebit*
        chown root.root ./bladebit*

        ln -s /opt/chia/bladebit/bladebit /usr/bin/bladebit
        cd / && echo "Bladebit version: "`bladebit --version`
        ln -s /opt/chia/bladebit/bladebit_cuda /usr/bin/bladebit_cuda
        cd / && echo "Bladebit CUDA version: "`bladebit_cuda --version`
    fi
fi
