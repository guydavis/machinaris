#!/bin/env bash
#
# Installs NChain as per https://gitee.com/ext9/ext9-blockchain
#

NCHAIN_BRANCH=$1

if [ -z ${NCHAIN_BRANCH} ]; then
	echo 'Skipping NChain install as not requested.'
else
	git clone --branch ${NCHAIN_BRANCH} https://gitee.com/ext9/ext9-blockchain.git  --recurse-submodules
	cd ext9-blockchain
	sh install.sh
	. ./activate
	chia start node
fi