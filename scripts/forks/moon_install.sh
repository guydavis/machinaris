#!/bin/env bash
#
# Installs Moon as per https://github.com/MOONCOINTEAM/moon-blockchain

MOON_BRANCH=$1
# On 2022-11-04
HASH=dbb7e66d4cb1af20caa3d8f3dc883a345d7643e3

if [ -z ${MOON_BRANCH} ]; then
    echo 'Skipping Moon install as not requested.'
else
    cd /
    rm -rf /root/.cache
    git clone --branch ${MOON_BRANCH} --single-branch https://github.com/MOONCOINTEAM/moon-blockchain.git /moon-blockchain
    cd /moon-blockchain 
    git submodule update --init mozilla-ca 
    git checkout $HASH
    pwd
    chmod +x install.sh

    # 2022-07-20: Python needs 'packaging==21.3'
    sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
    # 2022-06-17: Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' moon/wallet/wallet_state_manager.py
    # 2023-08-27: Python 3.10.8 broke old blockchain syncing. See: https://github.com/Chia-Network/chia-blockchain/pull/13638
    sed -i 's/waiter_count = len(self.full_node.new_peak_sem._waiters)/new_peak_sem = self.full_node.new_peak_sem\n        waiter_count = 0 if new_peak_sem._waiters is None else len(new_peak_sem._waiters)/g' moon/full_node/full_node_api.py
    sed -i 's/async with self.full_node.new_peak_sem:/async with new_peak_sem:/g' moon/full_node/full_node_api.py
    sed -i 's/if len(self.full_node.compact_vdf_sem._waiters) > 20:/compact_vdf_sem = self.full_node.compact_vdf_sem\n        waiter_count = 0 if compact_vdf_sem._waiters is None else len(compact_vdf_sem._waiters)\n        if waiter_count > 20:/g' moon/full_node/full_node_api.py

    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /moon-blockchain /chia-blockchain
        ln -s /moon-blockchain/venv/bin/moon /chia-blockchain/venv/bin/chia
    fi
fi
