#!/bin/env bash
#
# Installs Chia as per https://github.com/Chia-Network/chia-blockchain
#

CHIA_BRANCH=$1
# On 2022-03-08
HASH=0e7cc5a88393ef02b4057dd4bf894be2e73bc00b

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
