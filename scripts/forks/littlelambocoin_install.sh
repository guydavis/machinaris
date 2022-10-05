#!/bin/env bash
#
# Installs LittleLamboCoin as per https://github.com/BTCgreen-Network/littlelambocoin-blockchain
#

LITTLELAMBOCOIN_BRANCH=$1
# On 2022-10-04
HASH=5126d3af5901aa2d59fbe4e6e2716a2b0bfc88fb

if [ -z ${LITTLELAMBOCOIN_BRANCH} ]; then
	echo 'Skipping LittleLamboCoin install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${LITTLELAMBOCOIN_BRANCH} --single-branch https://github.com/BTCgreen-Network/littlelambocoin-blockchain /littlelambocoin-blockchain
	cd /littlelambocoin-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	# Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -e 's/^        self.log.debug($/        self.log.info(/g' littlelambocoin/wallet/wallet_state_manager.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /littlelambocoin-blockchain /chia-blockchain
		ln -s /littlelambocoin-blockchain/venv/bin/littlelambocoin /chia-blockchain/venv/bin/chia
	fi
fi
