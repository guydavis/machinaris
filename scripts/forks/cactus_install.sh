#!/bin/env bash
#
# Installs Cactus as per https://github.com/Cactus-Network/cactus-blockchain
#

CACTUS_BRANCH=$1
# On 2022-07-01
HASH=5279634186e1026e31ee67442b31150ff069db80

if [ -z ${CACTUS_BRANCH} ]; then
	echo 'Skipping Cactus install as not requested.'
else
	git clone --branch ${CACTUS_BRANCH} --recurse-submodules https://github.com/Cactus-Network/cactus-blockchain.git /cactus-blockchain 
	cd /cactus-blockchain 
	git submodule update --init mozilla-ca
	git checkout $HASH
	chmod +x install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /cactus-blockchain /chia-blockchain
		ln -s /cactus-blockchain/venv/bin/cactus /chia-blockchain/venv/bin/chia
	fi
fi
