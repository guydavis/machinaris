#!/bin/env bash
#
# At container launch on target user's system, this builds the bladebit
# codebase checked out on Github servers during image creation.  Due to
# issues with illegal instructions bladebit must be built on hardware it
# runs on. 
#

if [[ ${mode} == 'fullnode' ]] || [[ ${mode} =~ "plotter" ]]; then
    if [ ! -f /usr/bin/bladebit ]; then
        # Build the code, previously cloned when image was built on Github build servers
        arch_name="$(uname -m)"
        echo "arch_name=${arch_name}"
        if [[ "${arch_name}" = "x86_64" ]] || [[ "${arch_name}" = "arm64" ]]; then
            cd /bladebit && echo "Building bladebit on ${arch_name}..."
            mkdir -p build && cd build
            cmake ..
            cmake --build . --target bladebit --config Release
            ln -s /bladebit/build/bladebit /usr/bin/bladebit
            cd / && echo "Bladebit version: "`bladebit --version`
        else
            echo "Building bladebit skipped -> unsupported architecture: ${arch_name}"
        fi
    fi
fi
