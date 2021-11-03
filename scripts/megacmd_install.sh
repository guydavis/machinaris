#!/bin/env bash
#
# Installs megacmd for scripted downloads of pre-synced blockchains
# https://github.com/meganz/MEGAcmd 
# https://chiaforksblockchain.com/
#

arch_name="$(uname -m)"
echo "Installing megacmd on ${arch_name}..."
if [[ "${arch_name}" = "x86_64" ]]; then
    echo 'deb https://mega.nz/linux/MEGAsync/xUbuntu_21.04/ ./' > /etc/apt/sources.list.d/mega-nz.list 
	curl -fsSL https://mega.nz/keys/MEGA_signing.key | apt-key add - 
	apt-get update
	apt-get install -y megacmd
else
    echo "Installing megacmd skipped -> unsupported architecture: ${arch_name}"
fi
