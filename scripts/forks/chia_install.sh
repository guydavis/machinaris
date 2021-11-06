#!/bin/env bash
#
# Installs Chia as per https://github.com/Chia-Network/chia-blockchain
#

CHIA_BRANCH=$1
# On 2021-11-06
HASH=b74a3f3849cadeece2fac3efa3cb55d7d3a0647f

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
