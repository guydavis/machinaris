#!/bin/env bash
#
# Installs forktools - https://github.com/Qwinn1/forktools
#

# On 2021-11-17
HASH=65bf10c63e701de732b61b24fafeab03e6d1e695

if [[ ${mode} == 'fullnode' ]] || [[ ${mode} =~ "harvester" ]]; then
    cd /
	export FORKTOOLSBLOCKCHAINDIRS=/
	git clone https://github.com/Qwinn1/forktools
	cd forktools
	git checkout $HASH

	mkdir -p /root/.chia/forktools/ftconfigs
	cp -f ftconfigs/* /root/.chia/forktools/ftconfigs
	rm -rf ftconfigs
	ln -s /root/.chia/forktools/ftconfigs ftconfigs
	
	mkdir -p /root/.chia/forktools/ftlogs
	cp -f ftlogs/* /root/.chia/forktools/ftlogs
	rm -rf ftlogs
	ln -s /root/.chia/forktools/ftlogs ftlogs

	bash installft.sh
	source ~/.bashrc

	# Now multiproc patch fullnodes to limit memory usage
	if [[ ${mode} == 'fullnode' ]]; then
		./forkpatch all -multiproc
	fi
fi