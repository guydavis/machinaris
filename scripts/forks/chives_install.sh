#!/bin/env bash
#
# Installs Chives as per https://github.com/HiveProject2021/chives-blockchain
#

CHIVES_BRANCH=$1
# On 2022-05-22  Not used anymore
# HASH=c1111a79d7a1eb02a0bd2111307e266583bc67d1

if [ -z ${CHIVES_BRANCH} ]; then
	echo 'Skipping Chives install as not requested.'
else
	git clone --branch ${CHIVES_BRANCH} --recurse-submodules https://github.com/HiveProject2021/chives-blockchain.git /chives-blockchain 
	cd /chives-blockchain
	# Can't checkout due to filename limit issue with AUFS inside container
	#git checkout $HASH
	chmod +x install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /chives-blockchain /chia-blockchain
		ln -s /chives-blockchain/venv/bin/chives /chia-blockchain/venv/bin/chia
	fi
fi
