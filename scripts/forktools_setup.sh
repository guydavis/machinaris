#!/bin/env bash
#
# Installs forktools - https://github.com/Qwinn1/forktools
#

# On 2021-11-17
HASH=65bf10c63e701de732b61b24fafeab03e6d1e695

if [[ ${mode} == 'fullnode' ]] || [[ ${mode} =~ "harvester" ]]; then
    cd /
	git clone https://github.com/Qwinn1/forktools
	cd forktools
	bash installft.sh
	git checkout $HASH > /dev/null

	mkdir -p /root/.chia/forktools/ftconfigs
	cp -f ftconfigs/* /root/.chia/forktools/ftconfigs > /dev/null
	rm -rf ftconfigs
	ln -s /root/.chia/forktools/ftconfigs ftconfigs
	
	mkdir -p /root/.chia/forktools/ftlogs
	cp -f ftlogs/* /root/.chia/forktools/ftlogs > /dev/null
	rm -rf ftlogs
	ln -s /root/.chia/forktools/ftlogs ftlogs

	source ~/.bashrc

	# Now multiproc patch fullnodes to limit memory usage
	if [[ ${mode} == 'fullnode' ]]; then
		sed -i "s/SETMAXLOGROTATION='99'/SETMAXLOGROTATION='7' /g" /root/.chia/forktools/ftconfigs/config.forkfixconfig*
		sed -i "s/SETPLOTLOADFREQUENCY='18000'/SETPLOTLOADFREQUENCY='1800' /g" /root/.chia/forktools/ftconfigs/config.forkfixconfig*
		echo 'Y' | ./forkfixconfig all
		./forkpatch all -multiproc
	fi
fi