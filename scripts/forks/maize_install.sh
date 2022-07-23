#!/bin/env bash
#
# Installs Maize as per https://github.com/Maize-Network/maize-blockchain
#

MAIZE_BRANCH=$1
# On 2021-12-16
HASH=d6375e840084c269faadf6c511c9321180d17d13

if [ -z ${MAIZE_BRANCH} ]; then
	echo 'Skipping Maize install as not requested.'
else
	cd /
	rm -rf /root/.cache
	git clone --branch ${MAIZE_BRANCH} --single-branch https://github.com/Maize-Network/maize-blockchain.git /maize-blockchain
	cd /maize-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	pwd
	chmod +x install.sh
	# 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
	sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /maize-blockchain /chia-blockchain
		ln -s /maize-blockchain/venv/bin/maize /chia-blockchain/venv/bin/chia
	fi
fi
