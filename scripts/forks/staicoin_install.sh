#!/bin/env bash
#
# Installs Staicoin as per https://github.com/STATION-I/staicoin-blockchain
#

STAICOIN_BRANCH=$1
# On 2022-09-17
HASH=4808632d8147b1fb8ec9ec7aad5a80f86a509b3d

if [ -z ${STAICOIN_BRANCH} ]; then
	echo 'Skipping Staicoin install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${STAICOIN_BRANCH} --single-branch https://github.com/STATION-I/staicoin-blockchain.git /staicoin-blockchain
	cd /staicoin-blockchain
	git submodule update --init mozilla-ca
	chmod +x install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /staicoin-blockchain /chia-blockchain
		ln -s /staicoin-blockchain/venv/bin/staicoin /chia-blockchain/venv/bin/chia
	fi
fi
