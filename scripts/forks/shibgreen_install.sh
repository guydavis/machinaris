#!/bin/env bash
#
# Installs SHIBGreen as per https://github.com/BTCgreen-Network/shibgreen-blockchain
#

SHIBGREEN_BRANCH=$1
# On 2023-01-30
HASH=74e65f98ea2d94eb4f895acc5512efd17acbde3c

if [ -z ${SHIBGREEN_BRANCH} ]; then
    echo 'Skipping SHIBGreen install as not requested.'
else
    rm -rf /root/.cache
    git clone --branch ${SHIBGREEN_BRANCH} --single-branch https://github.com/BTCgreen-Network/shibgreen-blockchain /shibgreen-blockchain
    cd /shibgreen-blockchain 
    git submodule update --init mozilla-ca 
    git checkout $HASH
    chmod +x install.sh

    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' shibgreen/wallet/wallet_state_manager.py

    # 2022-07-20: Python needs 'packaging==21.3'
    sed -i 's/packaging==21.0/packaging==21.3/g' setup.py

    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /shibgreen-blockchain /chia-blockchain
        ln -s /shibgreen-blockchain/venv/bin/shibgreen /chia-blockchain/venv/bin/chia
    fi
fi
