#!/bin/env bash
#
# Installs Staicoin as per https://github.com/STATION-I/staicoin-blockchain
#

STAICOIN_BRANCH=$1
# On 2022-03-20
HASH=6096e50031e338d5e1770bdcdfca4c2d0d7a0754

if [ -z ${STAICOIN_BRANCH} ]; then
	echo 'Skipping Staicoin install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${STAICOIN_BRANCH} --single-branch https://github.com/STATION-I/staicoin-blockchain.git /staicoin-blockchain
	cd /staicoin-blockchain
	git submodule update --init mozilla-ca
	chmod +x install.sh
	# 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
	sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /staicoin-blockchain /chia-blockchain
		ln -s /staicoin-blockchain/venv/bin/staicoin /chia-blockchain/venv/bin/chia
	fi
fi
