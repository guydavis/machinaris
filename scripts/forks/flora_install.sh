#!/bin/env bash
#
# Installs Flora as per https://github.com/Flora-Network/flora-blockchain
#

FLORA_BRANCH=$1
# On 2021-11-06
HASH=f4da13dd7160de772ea5daa333984bed3882e84c

if [ -z ${FLORA_BRANCH} ]; then
	echo 'Skipping Flora install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${FLORA_BRANCH} --single-branch https://github.com/Flora-Network/flora-blockchain.git /flora-blockchain
	cd /flora-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh 
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /flora-blockchain /chia-blockchain
		ln -s /flora-blockchain/venv/bin/flora /chia-blockchain/venv/bin/chia
	fi
fi
