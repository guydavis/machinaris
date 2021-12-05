#!/bin/env bash
#
# Installs BTCGreen as per https://github.com/BTCgreen-Network/btcgreen-blockchain
#

BTCGREEN_BRANCH=$1
# On 2021-12-05
HASH=263e39a22a0415028b5989511302d351d7158b38

if [ -z ${BTCGREEN_BRANCH} ]; then
	echo 'Skipping BTCGreen install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${BTCGREEN_BRANCH} --single-branch https://github.com/BTCgreen-Network/btcgreen-blockchain.git /btcgreen-blockchain
	cd /btcgreen-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh 
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /btcgreen-blockchain /chia-blockchain
		ln -s /btcgreen-blockchain/venv/bin/btcgreen /chia-blockchain/venv/bin/chia
	fi
fi
