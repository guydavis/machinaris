#!/bin/env bash
#
# Installs Maize as per https://github.com/Maize-Network/maize-blockchain
#

MAIZE_BRANCH=$1
# On 2022-09-22
HASH=1530e15a5fba769f9387508e842121daca5d44e2

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
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	# Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -e 's/^        self.log.debug($/        self.log.info(/g' maize/wallet/wallet_state_manager.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /maize-blockchain /chia-blockchain
		ln -s /maize-blockchain/venv/bin/maize /chia-blockchain/venv/bin/chia
	fi
fi
