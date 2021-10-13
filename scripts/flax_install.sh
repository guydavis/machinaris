#!/bin/env bash
#
# Installs Flax as per https://github.com/Flax-Network/flax-blockchain
#

FLAX_BRANCH=$1

rm -rf /root/.cache
git clone --branch ${FLAX_BRANCH} --single-branch https://github.com/Flax-Network/flax-blockchain.git /flax-blockchain \
	&& cd /flax-blockchain \
	&& git submodule update --init mozilla-ca \
	&& chmod +x install.sh \
	&& sh ./install.sh
