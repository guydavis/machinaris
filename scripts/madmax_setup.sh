#!/bin/env bash
#
# Installs chia-plotter (pipelined multi-threaded) from binaries
#
# https://github.com/madMAx43v3r/chia-plotter
# https://github.com/madMAx43v3r/mmx-binaries
#

if [[ (${mode} == 'fullnode' || ${mode} =~ "plotter") && (${blockchains} == 'chia' || ${blockchains} == 'chives' || ${blockchains} == 'mmx') ]]; then
    if [ ! -f /usr/bin/chia_plot ] && [[ "${madmax_skip_build}" != 'true' ]]; then
        arch_name="$(uname -m)"
        if [[ "${arch_name}" = "x86_64" ]]; then
            pushd /usr/bin
            curl -sLJO https://github.com/madMAx43v3r/mmx-binaries/raw/master/mmx-cpu-plotter/linux/x86_64/chia_plot
            curl -sLJO https://github.com/madMAx43v3r/mmx-binaries/raw/master/mmx-cpu-plotter/linux/x86_64/chia_plot_k34
            chmod 755 chia_plot*
            curl -sLJO https://github.com/madMAx43v3r/mmx-binaries/raw/master/mmx-cuda-plotter/linux/x86_64/cuda_plot_k26
            curl -sLJO https://github.com/madMAx43v3r/mmx-binaries/raw/master/mmx-cuda-plotter/linux/x86_64/cuda_plot_k29
            curl -sLJO https://github.com/madMAx43v3r/mmx-binaries/raw/master/mmx-cuda-plotter/linux/x86_64/cuda_plot_k30
            curl -sLJO https://github.com/madMAx43v3r/mmx-binaries/raw/master/mmx-cuda-plotter/linux/x86_64/cuda_plot_k31
            curl -sLJO https://github.com/madMAx43v3r/mmx-binaries/raw/master/mmx-cuda-plotter/linux/x86_64/cuda_plot_k32
            curl -sLJO https://github.com/madMAx43v3r/mmx-binaries/raw/master/mmx-cuda-plotter/linux/x86_64/cuda_plot_k33
            chmod 755 cuda_plot*
            popd
        else
            echo "Downloading MMX chia_plot and cuda_plot skipped -> unsupported architecture: ${arch_name}"
        fi
    fi
fi
