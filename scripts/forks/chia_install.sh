#!/bin/env bash
#
# Installs Chia as per https://github.com/Chia-Network/chia-blockchain
#

CHIA_BRANCH=$1
# On 2022-04-03
HASH=0269797b0ae12add512c9a6c9a3ffe422724c4b9

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
