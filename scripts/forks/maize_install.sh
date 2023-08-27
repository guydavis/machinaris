#!/bin/env bash
#
# Installs Maize as per https://github.com/Maize-Network/maize-blockchain
#

MAIZE_BRANCH=$1
# On 2022-09-22
HASH=1530e15a5fba769f9387508e842121daca5d44e2

if [ -z ${MAIZE_BRANCH} ]; then
    echo 'Skipping Maize install as not requested.'
else
    cd /
    rm -rf /root/.cache
    git clone --branch ${MAIZE_BRANCH} --single-branch https://github.com/Maize-Network/maize-blockchain.git /maize-blockchain
    cd /maize-blockchain 
    git submodule update --init mozilla-ca 
    git checkout $HASH
    pwd
    chmod +x install.sh

    # 2022-07-20: Python needs 'packaging==21.3'
    sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
    # 2022-06-17: Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' maize/wallet/wallet_state_manager.py
    # 2023-08-27: Python 3.10.8 broke old blockchain syncing. See: https://github.com/Chia-Network/chia-blockchain/pull/13638
    sed -i 's/waiter_count = len(self.full_node.new_peak_sem._waiters)/new_peak_sem = self.full_node.new_peak_sem\n        waiter_count = 0 if new_peak_sem._waiters is None else len(new_peak_sem._waiters)/g' maize/full_node/full_node_api.py
    sed -i 's/async with self.full_node.new_peak_sem:/async with new_peak_sem:/g' maize/full_node/full_node_api.py
    sed -i 's/if len(self.full_node.compact_vdf_sem._waiters) > 20:/compact_vdf_sem = self.full_node.compact_vdf_sem\n        waiter_count = 0 if compact_vdf_sem._waiters is None else len(compact_vdf_sem._waiters)\n        if waiter_count > 20:/g' maize/full_node/full_node_api.py

    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /maize-blockchain /chia-blockchain
        ln -s /maize-blockchain/venv/bin/maize /chia-blockchain/venv/bin/chia
    fi
fi
