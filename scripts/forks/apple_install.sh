#!/bin/env bash
#
# Installs Apple as per https://github.com/Apple-Network/apple-blockchain
#

APPLE_BRANCH=$1
# On 2022-08-07
HASH=c65330e958fc5ed18a7afc267932065316468155

if [ -z ${APPLE_BRANCH} ]; then
	echo 'Skipping Apple install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${APPLE_BRANCH} --single-branch https://github.com/Apple-Network/apple-blockchain.git /apple-blockchain
	cd /apple-blockchain 
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
		ln -s /apple-blockchain /chia-blockchain
		ln -s /apple-blockchain/venv/bin/apple /chia-blockchain/venv/bin/chia
	fi
fi
