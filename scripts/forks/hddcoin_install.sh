#!/bin/env bash
#
# Installs HDDCoin as per git clone https://github.com/HDDcoin-Network/hddcoin-blockchain
#

HDDCOIN_BRANCH=$1
# On 2022-01-22
HASH=1b7f475af43dd251d6b8e866066a0834712f45ec

if [ -z ${HDDCOIN_BRANCH} ]; then
	echo 'Skipping HDDCoin install as not requested.'
else
	git clone --branch ${HDDCOIN_BRANCH} --recurse-submodules https://github.com/HDDcoin-Network/hddcoin-blockchain.git /hddcoin-blockchain
	cd /hddcoin-blockchain
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh
	# 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
	sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /hddcoin-blockchain /chia-blockchain
		ln -s /hddcoin-blockchain/venv/bin/hddcoin /chia-blockchain/venv/bin/chia
	fi
fi