#!/bin/env bash
#
# Installs Tad as per https://github.com/BTCgreen-Network/tad-blockchain
#

TAD_BRANCH=$1
# On 2022-11-04 - rolled back to v1.5.0 as v1.6.0 had code errors about included code on launch
HASH=80ccd218e21f71450420c88c4158bf3a43571caa

if [ -z ${TAD_BRANCH} ]; then
	echo 'Skipping Tad install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${TAD_BRANCH} --single-branch https://github.com/BTCgreen-Network/tad-blockchain.git /tad-blockchain
	cd /tad-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh

    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' tad/wallet/wallet_state_manager.py

	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py

	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /tad-blockchain /chia-blockchain
		ln -s /tad-blockchain/venv/bin/tad /chia-blockchain/venv/bin/chia
	fi
fi
