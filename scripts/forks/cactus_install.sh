#!/bin/env bash
#
# Installs Cactus as per https://github.com/Cactus-Network/cactus-blockchain
#

CACTUS_BRANCH=$1
# On 2022-07-23
HASH=50c18a15f0a63b4b90ad9efe2376c27c6c971dd4

if [ -z ${CACTUS_BRANCH} ]; then
	echo 'Skipping Cactus install as not requested.'
else
	git clone --branch ${CACTUS_BRANCH} --recurse-submodules https://github.com/Cactus-Network/cactus-blockchain.git /cactus-blockchain 
	cd /cactus-blockchain 
	git submodule update --init mozilla-ca
	git checkout $HASH
	chmod +x install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /cactus-blockchain /chia-blockchain
		ln -s /cactus-blockchain/venv/bin/cactus /chia-blockchain/venv/bin/chia
	fi
fi
