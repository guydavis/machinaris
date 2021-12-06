#!/bin/env bash
#
# Installs Chives as per https://github.com/HiveProject2021/chives-blockchain
#

CHIVES_BRANCH=$1
# On 2021-12-06
HASH=3d0f25cc04f8d4f527e90817916afa451d7ddf2b

if [ -z ${CHIVES_BRANCH} ]; then
	echo 'Skipping Chives install as not requested.'
else
	git clone --branch ${CHIVES_BRANCH} --recurse-submodules https://github.com/HiveProject2021/chives-blockchain.git /chives-blockchain 
	cd /chives-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh 
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /chives-blockchain /chia-blockchain
		ln -s /chives-blockchain/venv/bin/chives /chia-blockchain/venv/bin/chia
	fi
fi
