#!/bin/env bash
#
# Installs LittleLamboCoin as per https://github.com/BTCgreen-Network/littlelambocoin-blockchain
#

LITTLELAMBOCOIN_BRANCH=$1
# On 2022-07-28
HASH=60e010097e66fb9a56926f14e890d4d47f6ac465

if [ -z ${LITTLELAMBOCOIN_BRANCH} ]; then
	echo 'Skipping LittleLamboCoin install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${LITTLELAMBOCOIN_BRANCH} --single-branch https://github.com/BTCgreen-Network/littlelambocoin-blockchain /littlelambocoin-blockchain
	cd /littlelambocoin-blockchain 
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
		ln -s /littlelambocoin-blockchain /chia-blockchain
		ln -s /littlelambocoin-blockchain/venv/bin/littlelambocoin /chia-blockchain/venv/bin/chia
	fi
fi
