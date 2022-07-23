#!/bin/env bash
#
# Installs Silicoin as per https://github.com/silicoin-network/silicoin-blockchain
#

SILICOIN_BRANCH=$1
# On 2022-03-20
HASH=ebe7880e24b22d8f3bf8d0c8b31ad5397b3e7af3

if [ -z ${SILICOIN_BRANCH} ]; then
	echo 'Skipping Silicoin install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${SILICOIN_BRANCH} --single-branch https://github.com/silicoin-network/silicoin-blockchain /silicoin-blockchain
	cd /silicoin-blockchain 
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
		ln -s /silicoin-blockchain /chia-blockchain
		ln -s /silicoin-blockchain/venv/bin/sit /chia-blockchain/venv/bin/chia
	fi
fi
