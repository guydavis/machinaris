#!/bin/env bash
#
# Installs Chia as per https://github.com/Chia-Network/chia-blockchain/wiki/INSTALL#ubuntudebian
#

CHIA_BRANCH=$1

git clone --branch ${CHIA_BRANCH} --recurse-submodules https://github.com/Chia-Network/chia-blockchain.git /chia-blockchain \
	&& git checkout 89f7a4b3d6329493cd2b4bc5f346a819c99d3e7b \
	&& git submodule update --init mozilla-ca \
	&& chmod +x install.sh \
	&& /usr/bin/sh ./install.sh
