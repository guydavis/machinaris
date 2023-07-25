#!/bin/env bash
#
# Installs bladebit - A fast Chia plotter, offering disk, ram, and gpu modes.
# See https://github.com/Chia-Network/bladebit
#

BLADEBIT_BRANCH=$1  # Now ignored...

if [[ (${mode} =~ ^fullnode.*  || ${mode} =~ "plotter") && (${blockchains} == 'chia') ]]; then
    if [ ! -f /usr/bin/bladebit ] && [[ "${bladebit_skip_build}" != 'true' ]]; then
        arch_name="$(uname -m)"
        if [[ "${arch_name}" = "x86_64" ]] || [[ "${arch_name}" = "arm64" ]]; then
            apt update && apt install -y build-essential cmake libgmp-dev libnuma-dev
            cd /
            # Link to the bundled bladebit from Chia CLI DEB install...
            ln -s /opt/chia/bladebit/bladebit /usr/bin/bladebit
            cd / && echo "Bladebit version: "`bladebit --version`

            # Now install CNI's separate binary for actual GPU plotting...
            cd /opt/chia/bladebit
            if [[ "${arch_name}" = "x86_64" ]]; then
                curl -sLJO https://github.com/Chia-Network/bladebit/releases/download/v3.0.0-rc1/bladebit-cuda-v3.0.0-rc1-ubuntu-x86-64.tar.gz
            else
                curl -sLJO https://github.com/Chia-Network/bladebit/releases/download/v3.0.0-rc1/bladebit-cuda-v3.0.0-rc1-ubuntu-arm64.tar.gz
            fi
            tar -xvf *.tar.gz
            chmod 755 bladebit_cuda
            chown root.root ./bladebit*
            ln -s /opt/chia/bladebit/bladebit_cuda /usr/bin/bladebit_cuda
            cd / && echo "Bladebit CUDA version: "`bladebit_cuda --version`
        else
            echo "Bladebit binary download skipped -> unsupported architecture: ${arch_name}"
        fi
    fi
fi
