#!/bin/env bash
#
# Installs Flax as per https://github.com/Flax-Network/flax-blockchain
#

FLAX_BRANCH=$1
# On 2022-05-18
HASH=5a314ca5f7f12adb16db8a9a13366f0df14ad17d

if [ -z ${FLAX_BRANCH} ]; then
	echo 'Skipping Flax install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${FLAX_BRANCH} --single-branch https://github.com/Flax-Network/flax-blockchain.git /flax-blockchain
	cd /flax-blockchain
	git checkout $HASH
	git submodule update --init mozilla-ca
	chmod +x install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /flax-blockchain /chia-blockchain
		ln -s /flax-blockchain/venv/bin/flax /chia-blockchain/venv/bin/chia
	fi
fi
