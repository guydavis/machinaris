#!/bin/env bash
#
# Installs forktools - https://github.com/Qwinn1/forktools
#

FORKTOOLS_BRANCH=$1

if [[ "${forktools_skip_build}" != 'true' ]]; then
	if [[ (${mode} == 'fullnode' || ${mode} =~ "harvester") && ${blockchains} != 'mmx' ]]; then
		cd /
		git clone --branch ${FORKTOOLS_BRANCH} https://github.com/guydavis/forktools.git
		cd forktools
		bash installft.sh

		mkdir -p /root/.chia/forktools/ftconfigs
		cp -n ftconfigs/* /root/.chia/forktools/ftconfigs > /dev/null
		rm -rf ftconfigs
		ln -s /root/.chia/forktools/ftconfigs ftconfigs
		
		mkdir -p /root/.chia/forktools/ftlogs
		cp -f ftlogs/* /root/.chia/forktools/ftlogs > /dev/null
		rm -rf ftlogs
		ln -s /root/.chia/forktools/ftlogs ftlogs

		source ~/.bashrc

		# Now multiproc patch fullnodes to limit memory usage, but delay to offset resource crunch on launch
		if [[ ${mode} == 'fullnode' ]]; then
			echo 'Y' | ./forkfixconfig all
  			sleep $[ ( $RANDOM % 300 )  + 1 ]s
			./forkpatch all -multiproc || true
  			sleep $[ ( $RANDOM % 600 )  + 1 ]s
			./forkpatch all -logwinningplots || true
		fi
	fi
fi