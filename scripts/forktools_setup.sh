#!/bin/env bash
#
# Installs forktools - https://github.com/Qwinn1/forktools
#

if [[ ${mode} == 'fullnode' ]] || [[ ${mode} =~ "harvester" ]]; then
    if [[ ! -d /forktools ]]; then
		cd /
		export FORKTOOLSBLOCKCHAINDIRS=/
		git clone https://github.com/Qwinn1/forktools
		cd forktools
		bash installft.sh
		source ~/.bashrc
	fi
fi