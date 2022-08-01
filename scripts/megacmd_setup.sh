#!/bin/env bash
#
# Installs megacmd for scripted downloads of pre-synced blockchains, when requested
#
# https://github.com/meganz/MEGAcmd ; requires Ubuntu 22.04
#

if [[ ${mode} == 'fullnode' ]] && [[ "${blockchain_db_download}" == 'true' ]] && [[ ! -f /usr/bin/mega-cmd ]]; then
	arch_name="$(uname -m)"
	echo "Installing megacmd on ${arch_name}..."
	if [[ "${arch_name}" = "x86_64" ]]; then
		apt update
        apt install -y libc-ares2 libavcodec58 libavformat58 libavutil56 libswscale5 libmediainfo0v5 libzen0v5 libcrypto++8 libfreeimage3 libpcrecpp0v5
        cd /tmp && curl -O https://mega.nz/linux/repo/xUbuntu_22.04/amd64/megacmd_1.5.1-1.1_amd64.deb
		apt install -y ./megacmd_1.5.1-1.1_amd64.deb
	else
		echo "Installing megacmd skipped -> unsupported architecture: ${arch_name}"
	fi
fi