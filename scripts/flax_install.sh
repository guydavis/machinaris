#!/bin/env bash
#
# Installs Flax as per https://github.com/Flax-Network/flax-blockchain
#
FLAX_BRANCH=$1


if [ -z ${FLAX_BRANCH} ]; then
	echo 'Skipping Flax install as not requested.'
else
	cd /
	rm -rf /root/.cache
	git clone --branch ${FLAX_BRANCH} --single-branch https://github.com/Flax-Network/flax-blockchain.git /flax-blockchain \
		&& cd /flax-blockchain \
		&& git submodule update --init mozilla-ca \
		&& chmod +x install.sh \
		&& /usr/bin/sh ./install.sh

	echo "FLAX_FINISHED: checking root directory"
	ls -al /

	if [ ! -d /chia-blockchain]; then
		echo "Trying to link chia-blockchain"
		ln -s /flax-blockchain /chia-blockchain
	fi

	ls -al /
fi
