#!/bin/env bash
#
# Installs MMX as per https://github.com/madMAx43v3r/mmx-node
# using his binaries from https://github.com/madMAx43v3r/mmx-binaries.git
#

MMX_BRANCH=$1

if [ -z ${MMX_BRANCH} ]; then
    echo 'Skipping MMX install as not requested.'
else
    rm -rf /root/.cache
    apt-get update
    # Install dependencies for MMX
    apt-get install -y git cmake build-essential libsecp256k1-dev libsodium-dev libminiupnpc-dev libjemalloc-dev zlib1g-dev screen
    
    /usr/bin/bash /machinaris/scripts/gpu_drivers_install.sh

    # Clone and install MMX from the author's own binaries, not linked to his code branches unfortunately
    pushd /tmp
    git clone --branch ${MMX_BRANCH} --single-branch --depth 1 --filter=blob:none --sparse https://github.com/madMAx43v3r/mmx-binaries.git
    pushd mmx-binaries/
    git sparse-checkout set mmx-node/linux/x86_64/
    pushd mmx-node/linux
    mv x86_64 /mmx-node
    popd
    rm -f mmx-binaries
    popd
    tee /etc/ld.so.conf.d/30-mmx.conf >/dev/null <<EOF
/mmx-node/lib
EOF
    /usr/sbin/ldconfig
fi
