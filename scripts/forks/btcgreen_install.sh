#!/bin/env bash
#
# Installs BTCGreen as per https://github.com/BTCgreen-Network/btcgreen-blockchain
#

BTCGREEN_BRANCH=$1
# On 2022-08-09
HASH=487546c059083905b4417f361001e661be825ada

if [ -z ${BTCGREEN_BRANCH} ]; then
	echo 'Skipping BTCGreen install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${BTCGREEN_BRANCH} --single-branch https://github.com/BTCgreen-Network/btcgreen-blockchain.git /btcgreen-blockchain
	cd /btcgreen-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh

    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' btcgreen/wallet/wallet_state_manager.py

	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py

	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /btcgreen-blockchain /chia-blockchain
		ln -s /btcgreen-blockchain/venv/bin/btcgreen /chia-blockchain/venv/bin/chia
	fi
fi
