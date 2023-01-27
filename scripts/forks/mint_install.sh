#!/bin/env bash
#
# Installs Mint as per https://github.com/MintNetwork/mint-blockchain
#

MINT_BRANCH=$1
# On 2022-08-07
HASH=65ec05a015a07664ed25f83efa736065a17f7d7a

if [ -z ${MINT_BRANCH} ]; then
    echo 'Skipping Mint install as not requested.'
else
    rm -rf /root/.cache
    git clone --branch ${MINT_BRANCH} --single-branch https://github.com/MintNetwork/mint-blockchain.git /mint-blockchain
    cd /mint-blockchain 
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
        ln -s /mint-blockchain /chia-blockchain
        ln -s /mint-blockchain/venv/bin/mint /chia-blockchain/venv/bin/chia
    fi
fi
