#!/bin/env bash
#
# Installs HDDCoin as per git clone https://github.com/HDDcoin-Network/hddcoin-blockchain
#

HDDCOIN_BRANCH=$1

if [ -z ${HDDCOIN_BRANCH} ]; then
	echo 'Skipping HDDCoin install as not requested.'
else
	git clone --branch ${HDDCOIN_BRANCH} --recurse-submodules git clone https://github.com/HDDcoin-Network/hddcoin-blockchain.git /hddcoin-blockchain \
		&& cd /hddcoin-blockchain \
		&& git submodule update --init mozilla-ca \
		&& chmod +x install.sh \
		&& /usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /hddcoin-blockchain /chia-blockchain
	fi
fi