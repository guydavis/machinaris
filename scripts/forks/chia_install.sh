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

    /bin/sh ./install.sh

    # Drop GPU-enabled binaries in as well.
    arch_name="$(uname -m)"
    ubuntu_ver=`lsb_release -r -s`
    echo "Installing Chia CUDA binaries on ${arch_name}..."
    cd /tmp
    if [[ "${arch_name}" = "x86_64" ]]; then
        curl -sLJO https://github.com/Chia-Network/chia-blockchain/releases/download/2.1.0-rc2/chia-blockchain-cli_2.1.0rc2-1_amd64.deb
        apt-get install ./chia-blockchain-cli*.deb
    elif [[ "${arch_name}" = "arm64" ]]; then
        curl -sLJO https://github.com/Chia-Network/chia-blockchain/releases/download/2.1.0-rc2/chia-blockchain-cli_2.1.0rc2-1_arm64.deb
        apt-get install ./chia-blockchain-cli*.deb
    else
        echo "Installing Chia CUDA binaries skipped -> unsupported architecture: ${arch_name}"
    fi
fi
