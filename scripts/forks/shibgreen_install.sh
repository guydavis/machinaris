#!/bin/env bash
#
# Installs SHIBGreen as per https://github.com/SHIBgreen-Network/shibgreen-blockchain
#

SHIBGREEN_BRANCH=$1
# On 2021-12-06
HASH=2f72bf07bf9298668f7253587be64bb3dfac5c84

if [ -z ${SHIBGREEN_BRANCH} ]; then
	echo 'Skipping SHIBGreen install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${SHIBGREEN_BRANCH} --single-branch https://github.com/BTCgreen-Network/shibgreen-blockchain /shibgreen-blockchain
	cd /shibgreen-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh 
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /shibgreen-blockchain /chia-blockchain
		ln -s /shibgreen-blockchain/venv/bin/shibgreen /chia-blockchain/venv/bin/chia
	fi
fi
