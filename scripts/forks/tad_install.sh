#!/bin/env bash
#
# Installs Tad as per https://github.com/Tad-Network/tad-blockchain
#

TAD_BRANCH=$1
# On 2022-08-07
HASH=5fb43935cb741a820a1c10470cd6bff552e1a161

if [ -z ${TAD_BRANCH} ]; then
	echo 'Skipping Tad install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${TAD_BRANCH} --single-branch https://github.com/Tad-Network/tad-blockchain.git /tad-blockchain
	cd /tad-blockchain 
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
		ln -s /tad-blockchain /chia-blockchain
		ln -s /tad-blockchain/venv/bin/tad /chia-blockchain/venv/bin/chia
	fi
fi
