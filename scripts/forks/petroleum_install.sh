#!/bin/env bash
#
# Installs Petroleum as per https://github.com/petroleum-network/petroleum-blockchain
#

PETROLEUM_BRANCH=$1
# On 2022-07-05
HASH=670b48860d679712027afc2d477ab1db9c270755

if [ -z ${PETROLEUM_BRANCH} ]; then
	echo 'Skipping Petroleum install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${PETROLEUM_BRANCH} --single-branch https://github.com/petroleum-network/petroleum-blockchain /petroleum-blockchain
	cd /petroleum-blockchain 
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
		ln -s /petroleum-blockchain /chia-blockchain
		ln -s /petroleum-blockchain/venv/bin/sit /chia-blockchain/venv/bin/chia
	fi
fi
