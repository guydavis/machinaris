#!/bin/env bash
#
# Installs Silicoin as per https://github.com/silicoin-network/silicoin-blockchain
#

SILICOIN_BRANCH=$1
# On 2021-11-06
HASH=a433ae7bf997fd61979f0c995305678151b0317e

if [ -z ${SILICOIN_BRANCH} ]; then
	echo 'Skipping Silicoin install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${SILICOIN_BRANCH} --single-branch https://github.com/silicoin-network/silicoin-blockchain.git /silicoin-blockchain
	cd /silicoin-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh 
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /silicoin-blockchain /chia-blockchain
		ln -s /silicoin-blockchain/venv/bin/sit /silicoin-blockchain/venv/bin/silicoin
		ln -s /silicoin-blockchain/venv/bin/sit /chia-blockchain/venv/bin/chia
	fi
fi
