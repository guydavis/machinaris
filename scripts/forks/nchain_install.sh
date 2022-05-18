#!/bin/env bash
#
# Installs NChain as per https://gitee.com/ext9/ext9-blockchain
# NOTE: As of 2022-05-18, the Gitee repository went "member-only" whatever that means. 
#       So still using an old hash from 2021.  Seems like this blockchain fork is dead.
#

NCHAIN_BRANCH=$1
# On 2021-12-01
HASH=3c51a0bc6ee3930b40296a75dccf0ad8daab3a68

if [ -z ${NCHAIN_BRANCH} ]; then
	echo 'Skipping NChain install as not requested.'
else
	git clone --branch ${NCHAIN_BRANCH} --recurse-submodules https://gitee.com/ext9/ext9-blockchain.git /ext9-blockchain 
	cd /ext9-blockchain
	git submodule update --init mozilla-ca
	git checkout $HASH
	chmod +x install.sh
	# 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
	sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /ext9-blockchain /chia-blockchain
	fi
fi