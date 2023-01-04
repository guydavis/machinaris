#!/bin/env bash
#
# Installs Moon as per https://github.com/MOONCOINTEAM/moon-blockchain

MOON_BRANCH=$1
# On 2022-11-04
HASH=dbb7e66d4cb1af20caa3d8f3dc883a345d7643e3

if [ -z ${MOON_BRANCH} ]; then
	echo 'Skipping Moon install as not requested.'
else
	cd /
	rm -rf /root/.cache
	git clone --branch ${MOON_BRANCH} --single-branch https://github.com/MOONCOINTEAM/moon-blockchain.git /moon-blockchain
	cd /moon-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	pwd
	chmod +x install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	# Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -e 's/^        self.log.debug($/        self.log.info(/g' moon/wallet/wallet_state_manager.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /moon-blockchain /chia-blockchain
		ln -s /moon-blockchain/venv/bin/moon /chia-blockchain/venv/bin/chia
	fi
fi
