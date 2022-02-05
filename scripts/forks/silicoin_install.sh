#!/bin/env bash
#
# Installs Silicoin as per https://github.com/silicoin-network/silicoin-blockchain
#

SILICOIN_BRANCH=$1
# On 2022-02-05
HASH=ca482fa66f05e883891705c86bfdff63e101e3a4

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
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /silicoin-blockchain /chia-blockchain
		ln -s /silicoin-blockchain/venv/bin/sit /chia-blockchain/venv/bin/chia
	fi
fi
