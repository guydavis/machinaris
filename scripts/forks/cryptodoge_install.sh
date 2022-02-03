#!/bin/env bash
#
# Installs Cryptodoge as per https://github.com/CryptoDoge-Network/cryptodoge
#

CRYPTODOGE_BRANCH=$1
# On 2021-11-11
HASH=54926a63134e7aaa12e223afb0814583b779d17f

if [ -z ${CRYPTODOGE_BRANCH} ]; then
	echo 'Skipping Cryptodoge install as not requested.'
else
	git clone --branch ${CRYPTODOGE_BRANCH} --recurse-submodules https://github.com/CryptoDoge-Network/cryptodoge.git /cryptodoge-blockchain 
	cd /cryptodoge-blockchain
	git submodule update --init mozilla-ca
	git checkout $HASH
	chmod +x install.sh
	# 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
	sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /cryptodoge-blockchain /chia-blockchain
		ln -s /cryptodoge-blockchain/venv/bin/cryptodoge /chia-blockchain/venv/bin/chia
	fi
fi
