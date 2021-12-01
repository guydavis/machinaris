#!/bin/env bash
#
# Installs Maize as per https://github.com/Maize-Network/maize-blockchain
#

MAIZE_BRANCH=$1
# On 2021-12-01
HASH=b8639899f44b03232dda90c706d061e5e1158ca3

if [ -z ${MAIZE_BRANCH} ]; then
	echo 'Skipping Maize install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${MAIZE_BRANCH} --single-branch https://github.com/Maize-Network/maize-blockchain.git /maize-blockchain
	cd /maize-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh 
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /maize-blockchain /chia-blockchain
		ln -s /maize-blockchain/venv/bin/maize /chia-blockchain/venv/bin/chia
	fi
fi
