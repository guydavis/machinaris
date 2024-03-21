#!/bin/env bash
#
# Installs Madmax plotters:
#   * Classic open source for the default Chia image
#   * Closed source binary for the Madmax Gigahorse farmer image
#

# As of 2022-08-20
HASH=d1a9e88b44ba37f61bfabcb68e80e83f8b939648
CLASSIC_MADMAX_BRANCH=master

if [[ (${mode} =~ ^fullnode.*  || ${mode} =~ "plotter") && (${blockchains} == 'chia' || ${blockchains} == 'chives') ]]; then
    if [ ! -f /usr/bin/chia_plot ] && [[ "${madmax_skip_build}" != 'true' ]]; then
        arch_name="$(uname -m)"
        apt update && apt install -y libsodium-dev cmake g++ git build-essential
        cd /
        git clone --branch ${CLASSIC_MADMAX_BRANCH} https://github.com/madMAx43v3r/chia-plotter.git 
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
    fi
fi

# MMX Plotter binaries, https://github.com/madMAx43v3r/chia-gigahorse
# MMX and Gigahorse container gets the "new" Madmax plotters with compression, only available as binaries
if [[ (${mode} =~ ^fullnode.*  || ${mode} =~ "plotter") && (${blockchains} == 'mmx' || ${blockchains} == 'gigahorse') ]]; then
    if [ ! -f /usr/bin/chia_plot ] && [[ "${madmax_skip_build}" != 'true' ]]; then
        arch_name="$(uname -m)"
        if [[ "${arch_name}" == "x86_64" ]]; then
            pushd /usr/bin
            curl -sLJO https://github.com/madMAx43v3r/chia-gigahorse/raw/${GIGAHORSE_BRANCH}/cpu-plotter/linux/x86_64/chia_plot
            curl -sLJO https://github.com/madMAx43v3r/chia-gigahorse/raw/${GIGAHORSE_BRANCH}/cpu-plotter/linux/x86_64/chia_plot_k34
            chmod 755 chia_plot*
            curl -sLJO https://github.com/madMAx43v3r/chia-gigahorse/raw/${GIGAHORSE_BRANCH}/cuda-plotter/linux/x86_64/cuda_plot_k26
            curl -sLJO https://github.com/madMAx43v3r/chia-gigahorse/raw/${GIGAHORSE_BRANCH}/cuda-plotter/linux/x86_64/cuda_plot_k29
            curl -sLJO https://github.com/madMAx43v3r/chia-gigahorse/raw/${GIGAHORSE_BRANCH}/cuda-plotter/linux/x86_64/cuda_plot_k30
            curl -sLJO https://github.com/madMAx43v3r/chia-gigahorse/raw/${GIGAHORSE_BRANCH}/cuda-plotter/linux/x86_64/cuda_plot_k31
            curl -sLJO https://github.com/madMAx43v3r/chia-gigahorse/raw/${GIGAHORSE_BRANCH}/cuda-plotter/linux/x86_64/cuda_plot_k32
            curl -sLJO https://github.com/madMAx43v3r/chia-gigahorse/raw/${GIGAHORSE_BRANCH}/cuda-plotter/linux/x86_64/cuda_plot_k32_v3
            curl -sLJO https://github.com/madMAx43v3r/chia-gigahorse/raw/${GIGAHORSE_BRANCH}/cuda-plotter/linux/x86_64/cuda_plot_k33
            chmod 755 cuda_plot*
            curl -sLJO https://github.com/madMAx43v3r/chia-gigahorse/raw/${GIGAHORSE_BRANCH}/chiapos/linux/x86_64/ProofOfSpace
            chmod 755 ProofOfSpace
            popd
            echo "Completed download of Madmax binaries for plotting:"
            echo "chia_plot @ "`chia_plot --version`
            echo "cuda_plot_k32 @ "`cuda_plot_k32 --version`
            echo "cuda_plot_k32_v3 @ "`cuda_plot_k32_v3 --version`
        else
            echo "Downloading MMX chia_plot and cuda_plot skipped -> unsupported architecture: ${arch_name}"
        fi
    fi
fi
