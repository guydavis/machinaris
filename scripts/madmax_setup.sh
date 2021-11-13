#!/bin/env bash
#
# Installs chia-plotter (pipelined multi-threaded)
# See https://github.com/madMAx43v3r/chia-plotter
#

MADMAX_BRANCH=master

if [[ ${mode} == 'fullnode' ]] || [[ ${mode} =~ "plotter" ]]; then
    if [ ! -f /usr/bin/chia_plot ] && [[ -z "${madmax_skip_build}" ]]; then
        arch_name="$(uname -m)"
        if [[ "${arch_name}" = "x86_64" ]] || [[ "${arch_name}" = "arm64" ]]; then
            apt update && apt install -y libsodium-dev cmake g++ git build-essential
            cd /
            git clone --branch ${MADMAX_BRANCH} https://github.com/madMAx43v3r/chia-plotter.git 
            cd chia-plotter && echo "Building madmax on ${arch_name}..."
            git submodule update --init
            ./make_devel.sh
            mkdir -p /usr/lib/chia-plotter
            cp -r ./build/* /usr/lib/chia-plotter
            ln -s /usr/lib/chia-plotter/chia_plot /usr/bin/chia_plot
            ln -s /usr/lib/chia-plotter/chia_plot_k34 /usr/bin/chia_plot_k34
            cd /
            rm -rf chia-plotter
        else
            echo "Building madmax skipped -> unsupported architecture: ${arch_name}"
        fi
    fi
fi
