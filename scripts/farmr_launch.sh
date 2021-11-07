#!/bin/env bash
#
# If user has optionally enabled farmr by saving a config file, 
# then launch it on container start
#

# Only the /root/.chia folder is volume-mounted so store farmr within
mkdir -p /root/.chia/farmr
rm -f /root/.farmr
ln -s /root/.chia/farmr /root/.farmr 

cd /root/.farmr/blockchain
if [[ ${blockchains} == 'cactus' ]]; then
    cp -n cac.json.template cac.json
elif [[ ${blockchains} == 'chia' ]]; then
    cp -n xch.json.template xch.json
elif [[ ${blockchains} == 'chives' ]]; then
    cp -n xcc.json.template xcc.json
elif [[ ${blockchains} == 'flax' ]]; then
    cp -n xfx.json.template xfx.json
elif [[ ${blockchains} == 'flora' ]]; then
    cp -n xfl.json.template xfl.json
elif [[ ${blockchains} == 'hddcoin' ]]; then
    cp -n hdd.json.template hdd.json
elif [[ ${blockchains} == 'nchain' ]]; then
    cp -n nch.json.template nch.json
elif [[ ${blockchains} == 'silicoin' ]]; then
    cp -n sit.json.template sit.json
elif [[ ${blockchains} == 'staicoin' ]]; then
    cp -n stai.json.template stai.json
elif [[ ${blockchains} == 'stor' ]]; then
    cp -n stor.json.template stor.json
fi
cd /root/.farmr
nohup farmr &
