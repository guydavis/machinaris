#!/bin/env bash
#
# Installs bladebit - A fast RAM-only, k32-only, Chia plotter.
# 416 GiB of RAM are needed. See https://github.com/harold-b/bladebit
# NOTE: Bladebit checks proc count at build time, so must build when Docker first launched
#

if [ ! -f /usr/bin/bladebit ]; then
    # Build the code, previously cloned when image was built on Github build servers
    cd /bladebit
    ./build-bls
    make clean
    arch_name="$(uname -m)"
    echo "arch_name=${arch_name}"
    if [ "${arch_name}" = "x86_64" ]; then
        echo "Building bladebit on x86_64..."
        make -j$(nproc --all) 
        ln -s /bladebit/.bin/release/bladebit /usr/bin/bladebit
    elif [ "${arch_name}" = "arm64" ]; then
        echo "Building bladebit on arm64..."
        make -j$(nproc --all) CONFIG=release.arm 
        ln -s /bladebit/.bin/release.arm/bladebit /usr/bin/bladebit
    else
        echo "Building bladebit failed -> Unknown architecture: ${arch_name}"
        exit 1
    fi
    echo "Bladebit version: "`bladebit --version`
fi
