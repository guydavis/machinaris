#!/bin/env bash
#
# Installs chia-plotter (pipelined multi-threaded)
# See https://github.com/madMAx43v3r/chia-plotter
#

# As of 2022-08-20
HASH=d1a9e88b44ba37f61bfabcb68e80e83f8b939648
MADMAX_BRANCH=master

if [[ (${mode} == 'fullnode' || ${mode} =~ "plotter") && (${blockchains} == 'chia' || ${blockchains} == 'chives' || ${blockchains} == 'mmx') ]]; then
    if [ ! -f /usr/bin/chia_plot ] && [[ "${madmax_skip_build}" != 'true' ]]; then
        arch_name="$(uname -m)"
        if [[ "${arch_name}" = "x86_64" ]] || [[ "${arch_name}" = "arm64" ]]; then
            apt update && apt install -y libsodium-dev cmake g++ git build-essential
            cd /
            git clone --branch ${MADMAX_BRANCH} https://github.com/madMAx43v3r/chia-plotter.git 
            cd chia-plotter && echo "Building madmax on ${arch_name}..."
            if [[ -z "${madmax_relic_main}" ]]; then  # Hack on 2021-11-29 due to failed builds on some systems...
                sed -i 's/set(ENV{RELIC_MAIN} "1")/#set(ENV{RELIC_MAIN} "1")/g' CMakeLists.txt
            fi
            git submodule update --init
            git checkout $HASH
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
