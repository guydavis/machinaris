#!/bin/env bash
#
# Installs BPX as per https://github.com/bpx-network/bpx-blockchain
#

BPX_BRANCH=$1
# On 2022-07-08
HASH=9eb0d1b9421192b8c1afae9695e2c87944310719

if [ -z ${BPX_BRANCH} ]; then
	echo 'Skipping BPX install as not requested.'
else
	rm -rf /root/.cache
	git clone --branch ${BPX_BRANCH} --single-branch https://github.com/bpx-network/bpx-blockchain.git /bpx-blockchain
	cd /bpx-blockchain 
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
		ln -s /bpx-blockchain /chia-blockchain
		ln -s /bpx-blockchain/venv/bin/bpx /chia-blockchain/venv/bin/chia
	fi
fi
