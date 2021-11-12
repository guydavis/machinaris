#!/bin/env bash
#
# Installs Stor as per https://github.com/Stor-Network/stor-blockchain/wiki/INSTALL#ubuntudebian
#

STOR_BRANCH=$1
# On 2021-11-06
HASH=6edabce59a101a757c3269ab5a305259ddf95599

if [ -z ${STOR_BRANCH} ]; then
	echo 'Skipping Stor install as not requested.'
else
	git clone --branch ${STOR_BRANCH} --recurse-submodules https://github.com/Stor-Network/stor-blockchain.git /stor-blockchain 
	cd /stor-blockchain
	git submodule update --init mozilla-ca
	git checkout $HASH
	chmod +x install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /stor-blockchain /chia-blockchain
		ln -s /stor-blockchain/venv/bin/stor /chia-blockchain/venv/bin/chia
	fi
fi
