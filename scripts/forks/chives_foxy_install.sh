#!/bin/env bash
#
# Installs Chives as per https://github.com/foxypool/chives-blockchain
#

CHIVES_FOXY_BRANCH=$1

if [ -z ${CHIVES_FOXY_BRANCH} ]; then
	echo 'Skipping Chives install as not requested.'
else
	git clone --branch ${CHIVES_FOXY_BRANCH} --recurse-submodules https://github.com/foxypool/chives-blockchain.git /chives-foxy-blockchain
	cd /chives-foxy-blockchain
	chmod +x install.sh
	# 2022-07-20: Python needs 'packaging==21.3'
	sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
	/usr/bin/sh ./install.sh

	if [ ! -d /chia-blockchain/venv ]; then
		cd /
		rmdir /chia-blockchain
		ln -s /chives-foxy-blockchain /chia-blockchain
		ln -s /chives-foxy-blockchain/venv/bin/chives /chia-blockchain/venv/bin/chia
	fi
fi
