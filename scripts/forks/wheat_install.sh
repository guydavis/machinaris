#!/bin/env bash
#
# Installs Wheat as per https://github.com/wheatnetwork/wheat-blockchain
#

WHEAT_BRANCH=$1
# On 2022-08-07
HASH=65ec05a015a07664ed25f83efa736065a17f7d7a

if [ -z ${WHEAT_BRANCH} ]; then
	echo 'Skipping Wheat install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${WHEAT_BRANCH} --single-branch https://github.com/wheatnetwork/wheat-blockchain.git /wheat-blockchain
	cd /wheat-blockchain 
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
		ln -s /wheat-blockchain /chia-blockchain
		ln -s /wheat-blockchain/venv/bin/wheat /chia-blockchain/venv/bin/chia
	fi
fi
