#!/bin/env bash
#
# Installs SHIBGreen as per https://github.com/BTCgreen-Network/shibgreen-blockchain
#

SHIBGREEN_BRANCH=$1
# On 2022-03-20
HASH=b1e41e82ad849775543aa36fefc0c0d03e13f6e8

if [ -z ${SHIBGREEN_BRANCH} ]; then
	echo 'Skipping SHIBGreen install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${SHIBGREEN_BRANCH} --single-branch https://github.com/BTCgreen-Network/shibgreen-blockchain /shibgreen-blockchain
	cd /shibgreen-blockchain 
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
		ln -s /shibgreen-blockchain /chia-blockchain
		ln -s /shibgreen-blockchain/venv/bin/shibgreen /chia-blockchain/venv/bin/chia
	fi
fi
