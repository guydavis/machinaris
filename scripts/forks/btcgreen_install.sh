#!/bin/env bash
#
# Installs BTCGreen as per https://github.com/BTCgreen-Network/btcgreen-blockchain
#

BTCGREEN_BRANCH=$1
# On 2021-11-30
HASH=8edb226a904a0b947c269964951e5e0cd24539d3

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
