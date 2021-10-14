#!/bin/env bash
#
# Initialize Chives service, depending on mode of system requested
#


cd /chives-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store chives within
mkdir -p /root/.chia/chives
rm -f /root/.chives
ln -s /root/.chia/chives /root/.chives

mkdir -p /root/.chives/mainnet/log
chives init >> /root/.chives/mainnet/log/init.log 2>&1 

echo 'Configuring Chives...'
while [ ! -f /root/.chives/mainnet/config/config.yaml ]; do
  echo "Waiting for creation of /root/.chives/mainnet/config/config.yaml..."
  sleep 1
done
sed -i 's/log_stdout: true/log_stdout: false/g' /root/.chives/mainnet/config/config.yaml
sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.chives/mainnet/config/config.yaml

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [ -f ${k} ]; then
    echo "Adding key at path: ${k}"
    chives keys add -f ${k} > /dev/null
  else
    echo "Skipping 'chives keys add' as no file found at: ${k}"
  fi
done

# Loop over provided list of completed plot directories
for p in ${plots_dir//:/ }; do
    chives plots add -d ${p}
done

sed -i 's/localhost/127.0.0.1/g' ~/.chives/mainnet/config/config.yaml

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  if [ ! -f ~/.chives/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your mnemonic.txt to /root/.chia and restart."
  else
    chives start farmer
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.chives/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your mnemonic.txt to /root/.chia and restart."
  else
    chives start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.chives/farmer_ca/chives_ca.crt ]; then
      mkdir -p /root/.chives/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${controller_host}:8931/certificates/?type=chives --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.chives/farmer_ca
      else
        echo "Certificates response of ${response} from http://${controller_host}:8931/certificates/?type=chives.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip 
    fi
    if [ -f /root/.chives/farmer_ca/chives_ca.crt ]; then
      chives init -c /root/.chives/farmer_ca 2>&1 > /root/.chives/mainnet/log/init.log
    else
      echo "Did not find your farmer's certificates within /root/.chives/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    chives configure --set-farmer-peer ${farmer_address}:${farmer_port}
    chives configure --enable-upnp false
    chives start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
