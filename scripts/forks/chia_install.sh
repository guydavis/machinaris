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

    # 2022-07-08 - main branch is fully broken, with broken config loading, even using fresh config... *facepalm*
    # Reverting to commit a couple of days earlier on this branch to get a working blockchain again
    # https://github.com/Chia-Network/chia-blockchain/commit/383326c3b7fcd0d899950697e0766e11a2ce8c8b
    git checkout 383326c3b7fcd0d899950697e0766e11a2ce8c8b

    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' chia/wallet/wallet_state_manager.py

    /bin/sh ./install.sh
fi
