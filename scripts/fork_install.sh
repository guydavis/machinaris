#!/bin/env bash
# Universal Chia-/Fork installation script
#

## Via ENV:
#CHIA_FORK=$1
#FORK_BRANCH=$2
set -u

FORK_INSTALL_DIR=${FORK_INSTALL_DIR:-"/${CHIA_FORK}-blockchain"}

git clone --depth=1 --branch "${FORK_BRANCH}" "${FORK_REPO_URL}" "${FORK_INSTALL_DIR}"
cd "${FORK_INSTALL_DIR}"
git submodule update --init mozilla-ca

## Why? we already checked out the tag
#git -C /${CHIA_FORK}-blockchain checkout $FORK_HASH

# https://github.com/pypa/pip/issues/10825
sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
/bin/bash install.sh

if [ "${CHIA_FORK}" != "chia" ] && [ ! -d /chia-blockchain/venv ]; then
	rmdir /chia-blockchain 2>/dev/null
	ln -s "${FORK_INSTALL_DIR}" /chia-blockchain
	ln -s "${FORK_INSTALL_DIR}/venv/bin/${FORK_CMD}" /chia-blockchain/venv/bin/chia 2>/dev/null || true
fi
