#!/bin/env bash
#
# Installs Flax as per https://github.com/Flax-Network/flax-blockchain
#

if [ -z ${$1} ]; then
	echo 'Skipping Flax install as not requested.'
else

	FLAX_BRANCH=$1

	rm -rf /root/.cache
	git clone --branch ${FLAX_BRANCH} --single-branch https://github.com/Flax-Network/flax-blockchain.git /flax-blockchain \
		&& cd /flax-blockchain \
		&& git submodule update --init mozilla-ca \
		&& chmod +x install.sh \
		&& /usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain]; then
		ln -s /flax-blockchain /chia-blockchain
	fi
fi
