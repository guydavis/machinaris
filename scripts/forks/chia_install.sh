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

    curl -sLJO https://download.chia.net/bladebit/alpha4/chia-blockchain-cuda/ubuntu/chia-blockchain-cli_1.8.1rc2-dev34-1_amd64.deb
    apt-get install chia-blockchain*.deb
    ls -al /chia-blockchain

    # For testing of new GPU farming binaries, comment out build from source for now.
    #git clone --branch ${CHIA_BRANCH} --recurse-submodules=mozilla-ca https://github.com/Chia-Network/chia-blockchain.git /chia-blockchain
    #cd /chia-blockchain
    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    #sed -i -e 's/^        self.log.debug($/        self.log.info(/g' chia/wallet/wallet_state_manager.py
    #/bin/sh ./install.sh
fi
