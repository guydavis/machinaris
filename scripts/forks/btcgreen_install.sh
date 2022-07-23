#!/bin/env bash
#
# Installs BTCGreen as per https://github.com/BTCgreen-Network/btcgreen-blockchain
#

BTCGREEN_BRANCH=$1
# On 2022-03-20
HASH=f8c04e152ae17ee6893756d22db16ca700221b35

if [ -z ${BTCGREEN_BRANCH} ]; then
	echo 'Skipping BTCGreen install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${BTCGREEN_BRANCH} --single-branch https://github.com/BTCgreen-Network/btcgreen-blockchain.git /btcgreen-blockchain
	cd /btcgreen-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh
	# 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
	sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /btcgreen-blockchain /chia-blockchain
		ln -s /btcgreen-blockchain/venv/bin/btcgreen /chia-blockchain/venv/bin/chia
	fi
fi
