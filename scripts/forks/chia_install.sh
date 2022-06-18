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
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' chia/wallet/wallet_state_manager.py

    # 2022-06-18 - main branch is fully broken, just spinning on wallet_node calls, chewing all CPU
    # Reverting to commit about 3 days earlier on this branch to get a working blockchain again
    # https://github.com/Chia-Network/chia-blockchain/commit/61112a381dec2cd4f6f34a47e36ca400f10d8d74
    git checkout 61112a381dec2cd4f6f34a47e36ca400f10d8d74

    /bin/sh ./install.sh
fi
