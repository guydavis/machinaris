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
    apt-get update && apt-get install -y dialog apt-utils ca-certificates curl gnupg
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
    if [[ "${arch_name}" == "x86_64" ]]; then
        curl -sLJO https://github.com/Chia-Network/chia-blockchain/releases/download/2.2.0-rc4/chia-blockchain-cli_2.2.0rc4-1_amd64.deb
        apt-get install ./chia-blockchain-cli*.deb
    else
        curl -sLJO https://github.com/Chia-Network/chia-blockchain/releases/download/2.2.0-rc4/chia-blockchain-cli_2.2.0rc4-1_arm64.deb
        apt-get install ./chia-blockchain-cli*.deb
    fi

    # Also include "chia-exporter" for Prometheus reporting endpoints.
    curl -sL https://repo.chia.net/FD39E6D3.pubkey.asc | sudo gpg --dearmor -o /usr/share/keyrings/chia.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/chia.gpg] https://repo.chia.net/chia-exporter/debian/ stable main" | tee /etc/apt/sources.list.d/chia-exporter.list > /dev/null
    apt-get update
    apt-get install -y chia-exporter
fi
