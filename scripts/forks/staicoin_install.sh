#!/bin/env bash
#
# Installs Staicoin as per https://github.com/STATION-I/staicoin-blockchain
#

STAICOIN_BRANCH=$1
# On 2023-01-08
HASH=60b6a001795af56ed1b2fc6e464cdc10884193a1

if [ -z ${STAICOIN_BRANCH} ]; then
    echo 'Skipping Staicoin install as not requested.'
else
    rm -rf /root/.cache
    git clone --branch ${STAICOIN_BRANCH} --single-branch https://github.com/STATION-I/staicoin-blockchain.git /staicoin-blockchain
    cd /staicoin-blockchain
    git submodule update --init mozilla-ca
    chmod +x install.sh

    # 2022-07-20: Python needs 'packaging==21.3'
    sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
    # 2022-06-17: Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' stai/wallet/wallet_state_manager.py
    # 2023-08-27: Python 3.10.8 broke old blockchain syncing. See: https://github.com/Chia-Network/chia-blockchain/pull/13638
    sed -i 's/waiter_count = len(self.full_node.new_peak_sem._waiters)/new_peak_sem = self.full_node.new_peak_sem\n        waiter_count = 0 if new_peak_sem._waiters is None else len(new_peak_sem._waiters)/g' stai/full_node/full_node_api.py
    sed -i 's/async with self.full_node.new_peak_sem:/async with new_peak_sem:/g' stai/full_node/full_node_api.py
    sed -i 's/if len(self.full_node.compact_vdf_sem._waiters) > 20:/compact_vdf_sem = self.full_node.compact_vdf_sem\n        waiter_count = 0 if compact_vdf_sem._waiters is None else len(compact_vdf_sem._waiters)\n        if waiter_count > 20:/g' stai/full_node/full_node_api.py

    /usr/bin/sh ./install.sh

    arch_name="$(uname -m)"
    if [[ "${arch_name}" = "x86_64" ]]; then
        sh /machinaris/scripts/timelord_setup.sh
    fi

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /staicoin-blockchain /chia-blockchain
        ln -s /staicoin-blockchain/venv/bin/staicoin /chia-blockchain/venv/bin/chia
    fi
fi
