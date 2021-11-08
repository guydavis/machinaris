#!/bin/env bash
#
# If user has optionally enabled farmr by saving a config file, 
# then launch it on container start
#

# Only the /root/.chia folder is volume-mounted so store farmr within
mkdir -p /root/.chia/farmr
rm -f /root/.farmr
ln -s /root/.chia/farmr /root/.farmr 

cd /root/.farmr

if [[ ! -d ./blockchain ]]; then # Never run before, will create default configs
    nohup farmr & 
    sleep 60
    rm -f nohup.out
fi

if [[ ${blockchains} != "chia" ]] && [[ -f blockchain/xch.json ]]; then
    mv -f blockchain/xch.json blockchain/xch.json.template
fi

if [[ ${blockchains} == 'cactus' ]]; then
    cp -n blockchain/cac.json.template blockchain/cac.json
    echo "/cactus-blockchain/venv/bin/cactus" > override-cac-binary.txt
elif [[ ${blockchains} == 'chia' ]]; then
    cp -n blockchain/xch.json.template blockchain/xch.json
    echo "/chia-blockchain/venv/bin/chia" > override-xch-binary.txt
elif [[ ${blockchains} == 'chives' ]]; then
    cp -n blockchain/xcc.json.template blockchain/xcc.json
    echo "/chives-blockchain/venv/bin/chives" > override-xcc-binary.txt
elif [[ ${blockchains} == 'flax' ]]; then
    cp -n blockchain/xfx.json.template blockchain/xfx.json
    echo "/flax-blockchain/venv/bin/flax" > override-xfx-binary.txt
elif [[ ${blockchains} == 'flora' ]]; then
    cp -n blockchain/xfl.json.template blockchain/xfl.json
    echo "/flora-blockchain/venv/bin/flora" > override-xfl-binary.txt
elif [[ ${blockchains} == 'hddcoin' ]]; then
    cp -n blockchain/hdd.json.template blockchain/hdd.json
    echo "/hddcoin-blockchain/venv/bin/hddcoin" > override-hdd-binary.txt
elif [[ ${blockchains} == 'nchain' ]]; then
    cp -n blockchain/nch.json.template blockchain/nch.json
    echo "/chia-blockchain/venv/bin/chia" > override-nch-binary.txt
elif [[ ${blockchains} == 'silicoin' ]]; then
    cp -n blockchain/sit.json.template blockchain/sit.json
    echo "/sit-blockchain/venv/bin/sit" > override-sit-binary.txt
elif [[ ${blockchains} == 'staicoin' ]]; then
    cp -n blockchain/stai.json.template blockchain/stai.json
    echo "/stai-blockchain/venv/bin/stai" > override-stai-binary.txt
elif [[ ${blockchains} == 'stor' ]]; then
    cp -n blockchain/stor.json.template blockchain/stor.json
    echo "/stor-blockchain/venv/bin/stor" > override-stor-binary.txt
fi

# Use local file for configuration
#sed -i 's/"Online Config": true/"Online Config": false/g' blockchain/*.json

if [[ ! -z $"farmr_skip_launch" ]]; then
    rm nohup.out # Remove stale stdout logging
    # Launch in harvester or farmer mode
    if [[ ${mode} =~ ^harvester.* ]]; then
        nohup /usr/bin/farmr harvester headless &
    elif [[ ${mode} == 'farmer']] || [[ ${mode} == 'fullnode']] then
        nohup /usr/bin/farmr farmer headless &
    fi
fi