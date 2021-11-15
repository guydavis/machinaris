#!/bin/env bash
#
# For each CIFS share in the provided comma-separated list
#

if [[ ! -z ${remote_shares} ]]; then
    echo "Attempting remote share mount for ${remote_shares}"
    if [[ -s /root/.chia/smbcredentials.txt ]]; then
        for share in ${remote_shares//,/ }; do
            remote="$(cut -d ':' -f1 <<<${share})"
            path="$(cut -d ':' -f2 <<<${share})"
            echo "mount -t cifs -o credentials=/root/.chia/smbcredentials.txt ${remote} ${path}"
            mount -t cifs -o credentials=/root/.chia/smbcredentials.txt ${remote} ${path}
        done
    else
        echo "No /root/.chia/smbcredentials.txt file found.  Please create one as per: https://github.com/guydavis/machinaris/wiki/Windows#network-share-access"
    fi
fi
