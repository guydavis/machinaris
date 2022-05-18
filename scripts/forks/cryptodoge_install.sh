#!/bin/env bash
#
# Installs Cryptodoge as per https://github.com/CryptoDoge-Network/cryptodoge
#

CRYPTODOGE_BRANCH=$1
# On 2022-05-18
HASH=4ec389b615b9054afcf43d14f7d18434b6b4d2de

if [ -z ${CRYPTODOGE_BRANCH} ]; then
	echo 'Skipping Cryptodoge install as not requested.'
else
	git clone --branch ${CRYPTODOGE_BRANCH} --recurse-submodules https://github.com/CryptoDoge-Network/cryptodoge.git /cryptodoge-blockchain 
	cd /cryptodoge-blockchain
	git submodule update --init mozilla-ca
	git checkout $HASH
	chmod +x install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /cryptodoge-blockchain /chia-blockchain
		ln -s /cryptodoge-blockchain/venv/bin/cryptodoge /chia-blockchain/venv/bin/chia
	fi
fi
