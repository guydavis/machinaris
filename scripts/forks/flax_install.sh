#!/bin/env bash
#
# Installs Flax as per https://github.com/Flax-Network/flax-blockchain
#

FLAX_BRANCH=$1
# On 2022-08-24
HASH=e8ad8e71e006f3b9239d339ca8b76372a8940f9e

if [ -z ${FLAX_BRANCH} ]; then
	echo 'Skipping Flax install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${FLAX_BRANCH} --single-branch https://github.com/Flax-Network/flax-blockchain.git /flax-blockchain
	cd /flax-blockchain
	git checkout $HASH
	git submodule update --init mozilla-ca
	chmod +x install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	# Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -e 's/^        self.log.debug($/        self.log.info(/g' flax/wallet/wallet_state_manager.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /flax-blockchain /chia-blockchain
		ln -s /flax-blockchain/venv/bin/flax /chia-blockchain/venv/bin/chia
	fi
fi
