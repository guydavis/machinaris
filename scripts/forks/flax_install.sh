#!/bin/env bash
#
# Installs Flax as per https://github.com/Flax-Network/flax-blockchain
#

FLAX_BRANCH=$1
# On 2022-03-13
HASH=e72b47ca1c7086330b0facba6a2e7fc5967000eb

if [ -z ${FLAX_BRANCH} ]; then
	echo 'Skipping Flax install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${FLAX_BRANCH} --single-branch https://github.com/Flax-Network/flax-blockchain.git /flax-blockchain
	cd /flax-blockchain
	git checkout $HASH
	git submodule update --init mozilla-ca
	chmod +x install.sh
	# 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
	sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /flax-blockchain /chia-blockchain
		ln -s /flax-blockchain/venv/bin/flax /chia-blockchain/venv/bin/chia
	fi
fi
