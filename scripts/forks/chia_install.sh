#!/bin/env bash
#
# Installs Chia as per https://github.com/Chia-Network/chia-blockchain
#

CHIA_BRANCH=$1
# On 2022-04-19
HASH=0f5a6df4ffcd7b1d5b950b9f40c15b4e6045ee1b

if [ -z ${CHIA_BRANCH} ]; then
    echo 'Skipping Chia install as not requested.'
else
    git clone --branch ${CHIA_BRANCH} --recurse-submodules https://github.com/Chia-Network/chia-blockchain.git /chia-blockchain
    cd /chia-blockchain
    git submodule update --init mozilla-ca 
    git checkout $HASH
    chmod +x install.sh
    /usr/bin/sh ./install.sh
fi
