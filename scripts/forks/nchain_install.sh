#!/bin/env bash
#
# Installs NChain as per https://gitee.com/ext9/ext9-blockchain
#

NCHAIN_BRANCH=$1

if [ -z ${NCHAIN_BRANCH} ]; then
	echo 'Skipping NChain install as not requested.'
else
	git clone --branch ${NCHAIN_BRANCH} --recurse-submodules https://gitee.com/ext9/ext9-blockchain.git /ext9-blockchain \
		&& cd /ext9-blockchain \
		&& git submodule update --init mozilla-ca \
		&& chmod +x install.sh \
		&& /usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /ext9-blockchain /chia-blockchain
	fi
fi