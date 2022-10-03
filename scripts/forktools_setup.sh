#!/bin/env bash
#
# Installs forktools - https://github.com/Qwinn1/forktools
#

FORKTOOLS_BRANCH=testing

if [[ "${forktools_skip_build}" != 'true' ]]; then
	if [[ (${mode} == 'fullnode' || ${mode} =~ "harvester") && ${blockchains} != 'mmx' ]]; then
		cd /
		git clone --branch ${FORKTOOLS_BRANCH} git@github.com:guydavis/forktools.git
		cd forktools
		bash installft.sh
		git checkout $HASH > /dev/null

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
			if [ ! -f /root/.chia/forktools/ftconfigs/.configured ]; then
				sed -i "s/SETMAXLOGROTATION='99'/SETMAXLOGROTATION='7'/g" /root/.chia/forktools/ftconfigs/config.forkfixconfig*
				sed -i "s/SETPLOTLOADFREQUENCY='18000'/SETPLOTLOADFREQUENCY='1800'/g" /root/.chia/forktools/ftconfigs/config.forkfixconfig*
				sed -i "s/SETFNTARGETPEERCOUNT='80'/SETFNTARGETPEERCOUNT='20'/g"  /root/.chia/forktools/ftconfigs/config.forkfixconfig*
				sed -i "s/\"/'/g" /root/.chia/forktools/ftconfigs/config.forkfixconfig
				touch /root/.chia/forktools/ftconfigs/.configured
			fi
			echo 'Y' | ./forkfixconfig all
  			sleep $[ ( $RANDOM % 300 )  + 1 ]s
			./forkpatch all -multiproc || true
  			sleep $[ ( $RANDOM % 600 )  + 1 ]s
			./forkpatch all -logwinningplots || true
		fi
	fi
fi