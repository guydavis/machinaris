#!/bin/env bash
#
# Installs Chia as per https://github.com/Chia-Network/chia-blockchain
#

CHIA_BRANCH=$1

if [ -z ${CHIA_BRANCH} ]; then
    echo 'Skipping Chia install as not requested.'
else
    cd /tmp
    rm -rf /root/.cache
    apt-get update && apt-get install -y dialog apt-utils
    /usr/bin/bash /machinaris/scripts/gpu_drivers_install.sh

    git clone --branch ${CHIA_BRANCH} --recurse-submodules=mozilla-ca https://github.com/Chia-Network/chia-blockchain.git /chia-blockchain
    cd /chia-blockchain

    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' chia/wallet/wallet_state_manager.py

    # Now correct the version that Chia binaries report.  Use the actual version checked out from Github.
    branch_version=$(echo $CHIA_BRANCH | grep -Po '(?<=release/)\d.\d.\d')
    if [ $? -eq 0 ]; then # Will match if branch is "release/X.Y.Z", not if branch is "main" (development stream)
        echo "Building Chia release version ${branch_version}"
        sed -i "/name=\"chia-blockchain\",/a \ \ \ \ version=\"${branch_version}\"," setup.py
    else
        echo "Building Chia development version from branch ${CHIA_BRANCH}"
    fi

    /bin/sh ./install.sh

fi
