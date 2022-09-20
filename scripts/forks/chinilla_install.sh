#!/bin/env bash
#
# Installs Chinilla as per https://github.com/Chinilla/chinilla-blockchain
#

CHINILLA_BRANCH=$1
# On 2022-08-20
HASH=eabbe663cb5aaa30f5748209b856c4271cb8f584

if [ -z ${CHINILLA_BRANCH} ]; then
	echo 'Skipping Chinilla install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${CHINILLA_BRANCH} --single-branch https://github.com/Chinilla/chinilla-blockchain.git /chinilla-blockchain
	cd /chinilla-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	# Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -e 's/^        self.log.debug($/        self.log.info(/g' chinilla/wallet/wallet_state_manager.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /chinilla-blockchain /chia-blockchain
		ln -s /chinilla-blockchain/venv/bin/chinilla /chia-blockchain/venv/bin/chia
	fi
fi
