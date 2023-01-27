#!/bin/env bash
#
# Installs Profit as per https://github.com/ProfitCrypto/profit-blockchain
#

PROFIT_BRANCH=$1
# On 2022-07-20
HASH=966811500810a0dcbf13a8e02f507b9449bb418c

if [ -z ${PROFIT_BRANCH} ]; then
    echo 'Skipping Profit install as not requested.'
else
    rm -rf /root/.cache
    git clone --branch ${PROFIT_BRANCH} --single-branch https://github.com/ProfitCrypto/profit-blockchain /profit-blockchain
    cd /profit-blockchain 
    git submodule update --init mozilla-ca 
    git checkout $HASH
    chmod +x install.sh
    # 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
    sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
    # 2022-07-20: Python needs 'packaging==21.3'
    sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /profit-blockchain /chia-blockchain
        ln -s /profit-blockchain/venv/bin/sit /chia-blockchain/venv/bin/chia
    fi
fi
