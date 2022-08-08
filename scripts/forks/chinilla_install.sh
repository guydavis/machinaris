#!/bin/env bash
#
# Installs Chinilla as per https://github.com/chinilla/chinilla-blockchain
#

CHINILLA_BRANCH=$1
# On 2022-08-07
HASH=9c96494c576e112e093d5c7fbab0db531b12bbf8

if [ -z ${CHINILLA_BRANCH} ]; then
	echo 'Skipping Chinilla install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${CHINILLA_BRANCH} --single-branch https://github.com/chinilla/chinilla-blockchain.git /chinilla-blockchain
	cd /chinilla-blockchain 
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
		ln -s /chinilla-blockchain /chia-blockchain
		ln -s /chinilla-blockchain/venv/bin/chinilla /chia-blockchain/venv/bin/chia
	fi
fi
