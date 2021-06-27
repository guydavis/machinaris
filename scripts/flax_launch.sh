#!/bin/env bash
#
# Initialize Flax service, depending on mode of system requested
#

cd /flax-blockchain

. ./activate

mkdir -p /root/.flax/mainnet/log
flax init >> /root/.flax/mainnet/log/init.log 2>&1 

echo 'Configuring Flax...'
sed -i 's/log_stdout: true/log_stdout: false/g' /root/.flax/mainnet/config/config.yaml
sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.flax/mainnet/config/config.yaml

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [ -f ${k} ]; then
    echo "Adding key at path: ${k}"
    flax keys add -f ${k} > /dev/null
  else
    echo "Skipping 'flax keys add' as no file found at: ${k}"
  fi
done

# Loop over provided list of completed plot directories
for p in ${plots_dir//:/ }; do
    flax plots add -d ${p}
done

sed -i 's/localhost/127.0.0.1/g' ~/.flax/mainnet/config/config.yaml

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  flax start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  flax start farmer-only
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ -d /root/.flax/farmer_ca ]; then
      flax init -c /root/.flax/farmer_ca 2>&1 > /root/.flax/mainnet/log/init.log
    else
      echo "Did not find your farmer's ca folder at /root/.flax/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    flax configure --set-farmer-peer ${farmer_address}:${farmer_port}
    flax configure --enable-upnp false
    flax start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
