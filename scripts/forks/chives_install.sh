#!/bin/env bash
#
# Installs Chives as per https://github.com/HiveProject2021/chives-blockchain
#

CHIVES_BRANCH=$1

if [ -z ${CHIVES_BRANCH} ]; then
	echo 'Skipping Chives install as not requested.'
else
	git clone --branch ${CHIVES_BRANCH} --recurse-submodules https://github.com/HiveProject2021/chives-blockchain.git /chives-blockchain \
		&& cd /chives-blockchain \
		&& git submodule update --init mozilla-ca \
		&& chmod +x install.sh \
		&& /usr/bin/sh ./install.sh
fi
