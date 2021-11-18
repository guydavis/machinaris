#!/bin/env bash
#
# Installs forktools - https://github.com/Qwinn1/forktools
#

# On 2021-11-17
HASH=65bf10c63e701de732b61b24fafeab03e6d1e695

if [[ ${mode} == 'fullnode' ]] || [[ ${mode} =~ "harvester" ]]; then
	cd /root/.chia
    if [[ ! -d /root/.chia/forktools ]]; then  # fresh install
		export FORKTOOLSBLOCKCHAINDIRS=/
		git clone https://github.com/Qwinn1/forktools
	fi
	cd forktools
	git checkout $HASH
	chmod +x $PWD/install*.sh
	$PWD/install2ft.sh
	source ~/.bashrc

	# Now multiproc patch fullnodes to limit memory usage
	if [[ ${mode} == 'fullnode' ]]; then
		./forkpatch all -multiproc
	fi
fi
