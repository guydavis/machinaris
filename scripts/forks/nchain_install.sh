#!/bin/env bash
#
# Installs NChain as per https://gitee.com/ext9/ext9-blockchain
#

NCHAIN_BRANCH=$1
# On 2021-12-01
HASH=2F3c51a0bc6ee3930b40296a75dccf0ad8daab3a68

if [ -z ${NCHAIN_BRANCH} ]; then
	echo 'Skipping NChain install as not requested.'
else
	git clone --branch ${NCHAIN_BRANCH} --recurse-submodules https://gitee.com/ext9/ext9-blockchain.git /ext9-blockchain 
	cd /ext9-blockchain
	git submodule update --init mozilla-ca
	git checkout $HASH
	chmod +x install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /ext9-blockchain /chia-blockchain
	fi
fi