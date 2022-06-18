#!/bin/env bash
#
# Installs Chia as per https://github.com/Chia-Network/chia-blockchain
#

CHIA_BRANCH=$1

if [ -z ${CHIA_BRANCH} ]; then
    echo 'Skipping Chia install as not requested.'
else
    git clone --branch ${CHIA_BRANCH} --recurse-submodules=mozilla-ca https://github.com/Chia-Network/chia-blockchain.git /chia-blockchain
    cd /chia-blockchain

    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -e 's/^        self.log.debug($/        self.log.info(/g' chia/wallet/wallet_state_manager.py > chia/wallet/wallet_state_manager.py.patched

    /bin/sh ./install.sh
fi
