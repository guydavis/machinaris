#!/bin/env bash
#
# Installs Apple as per https://github.com/Apple-Network/apple-blockchain
#

APPLE_BRANCH=$1
# On 2022-08-20
HASH=c4884b2774d1cf4a9ff8816ecd7b4e6676335c2c

if [ -z ${APPLE_BRANCH} ]; then
	echo 'Skipping Apple install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${APPLE_BRANCH} --single-branch https://github.com/Apple-Network/apple-blockchain.git /apple-blockchain
	cd /apple-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	# Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -e 's/^        self.log.debug($/        self.log.info(/g' apple/wallet/wallet_state_manager.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /apple-blockchain /chia-blockchain
		ln -s /apple-blockchain/venv/bin/apple /chia-blockchain/venv/bin/chia
	fi
fi
