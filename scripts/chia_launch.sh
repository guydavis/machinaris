#!/bin/env bash
#
# Initialize Chia service, depending on mode of system requested
#


cd /chia-blockchain

. ./activate

mkdir -p /root/.chia/mainnet/log
chia init >> /root/.chia/mainnet/log/init.log 2>&1 

echo 'Configuring Chia...'
sed -i 's/log_stdout: true/log_stdout: false/g' /root/.chia/mainnet/config/config.yaml
sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.chia/mainnet/config/config.yaml

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [ -f ${k} ]; then
    echo "Adding key at path: ${k}"
    chia keys add -f ${k} > /dev/null
  else
    echo "Skipping 'chia keys add' as no file found at: ${k}"
  fi
done

# Loop over provided list of completed plot directories
for p in ${plots_dir//:/ }; do
    chia plots add -d ${p}
done



sed -i 's/localhost/127.0.0.1/g' ~/.chia/mainnet/config/config.yaml

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  chia start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  chia start farmer-only
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ -d /root/.chia/farmer_ca ]; then
      chia init -c /root/.chia/farmer_ca 2>&1 > /root/.chia/mainnet/log/init.log
    else
      echo "Did not find your farmer's ca folder at /root/.chia/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    chia configure --set-farmer-peer ${farmer_address}:${farmer_port}
    chia configure --enable-upnp false
    chia start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
