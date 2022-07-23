#!/bin/env bash
#
# Installs Ecostake as per https://github.com/ecostake-network/ecostake-blockchain
#

ECOSTAKE_BRANCH=$1
# On 2022-07-05
HASH=8ea8bb9743c7caccb2f8c670853d93ee12d00c86

if [ -z ${ECOSTAKE_BRANCH} ]; then
	echo 'Skipping Ecostake install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${ECOSTAKE_BRANCH} --single-branch https://github.com/ecostake-network/ecostake-blockchain /ecostake-blockchain
	cd /ecostake-blockchain 
	git submodule update --init mozilla-ca 
	git checkout $HASH
	chmod +x install.sh
	# 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
	sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /ecostake-blockchain /chia-blockchain
		ln -s /ecostake-blockchain/venv/bin/sit /chia-blockchain/venv/bin/chia
	fi
fi
