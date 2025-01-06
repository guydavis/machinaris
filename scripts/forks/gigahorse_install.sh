#!/bin/env bash
#
# Installs Gigahorse as per https://github.com/madMAx43v3r/chia-gigahorse
#

GIGAHORSE_BRANCH=$1
GIGAHORSE_VERSION=${GIGAHORSE_BRANCH#?}  # Strip off the leading 'v' from his branch

if [ -z ${GIGAHORSE_BRANCH} ]; then
    echo 'Skipping Gigahorse install as not requested.'
else
    cd /tmp
    rm -rf /root/.cache
	apt-get update && apt-get install -y dialog apt-utils libgomp1
    /usr/bin/bash /machinaris/scripts/gpu_drivers_install.sh
	
    arch_name="$(uname -m)"
    if [[ "${arch_name}" == "x86_64" ]]; then
        url="https://github.com/madMAx43v3r/chia-gigahorse/releases/download/${GIGAHORSE_BRANCH}/chia-gigahorse-farmer-${GIGAHORSE_VERSION}-x86_64.tar.gz"
        echo "Pulling Madmax closed-source Chia farming binary from..."
        echo ${url}
        cd / && curl --retry 5 --retry-max-time 120 -skJLO ${url}
        du -hsc chia-gigahorse-farmer*
        tar -xzf chia-gigahorse-farmer*
    else
        # Max broke ARM64 support in v2.4.4.giga36, have to downgrade to 2.4.1
        if [[ "${GIGAHORSE_BRANCH}" == "v2.5.0.giga36" ]]; then
            GIGAHORSE_BRANCH="v2.4.1.giga36"  # old version
            GIGAHORSE_VERSION=${GIGAHORSE_BRANCH#?}
        fi
        url="https://github.com/madMAx43v3r/chia-gigahorse/releases/download/${GIGAHORSE_BRANCH}/chia-gigahorse-farmer-${GIGAHORSE_VERSION}-aarch64.tar.gz"
        echo "Pulling Madmax closed-source Chia farming binary from..."
        echo ${url}
        cd / && curl --retry 5 --retry-max-time 120 -skJLO ${url}
        du -hsc chia-gigahorse-farmer*
        tar -xzf chia-gigahorse-farmer*
    fi
fi
