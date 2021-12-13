#!/bin/env bash
#
# Installs SHIBGreen as per https://github.com/SHIBgreen-Network/shibgreen-blockchain
#

SHIBGREEN_BRANCH=$1
# On 2021-12-12
HASH=d2e08a3cad84b1cb72c7952c9870aa44ff9d7104

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
