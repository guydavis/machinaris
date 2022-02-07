#!/bin/env bash
#
# Installs Chia as per https://github.com/Chia-Network/chia-blockchain
#

CHIA_BRANCH=$1
# On 2022-02-07
HASH=f2fe1dca6266f9b1f8ab61798ad40e5985f50b23

if [ -z ${CHIA_BRANCH} ]; then
	echo 'Skipping Chia install as not requested.'
else
	git clone --branch ${CHIA_BRANCH} --recurse-submodules https://github.com/Chia-Network/chia-blockchain.git /chia-blockchain
	cd /chia-blockchain
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh
	# 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
	#sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
	/usr/bin/sh ./install.sh
fi
