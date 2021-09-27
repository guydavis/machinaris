#!/bin/env bash
#
# Initialize Chia service, depending on mode of system requested
#


cd /hddcoin-blockchain

. ./activate

mkdir -p /root/.hddcoin/mainnet/log
chia init >> /root/.hddcoin/mainnet/log/init.log 2>&1 

echo 'Configuring Chia...'
while [ ! -f /root/.hddcoin/mainnet/config/config.yaml ]; do
  echo "Waiting for creation of /root/.hddcoin/mainnet/config/config.yaml..."
  sleep 1
done
sed -i 's/log_stdout: true/log_stdout: false/g' /root/.hddcoin/mainnet/config/config.yaml
sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.hddcoin/mainnet/config/config.yaml

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

sed -i 's/localhost/127.0.0.1/g' ~/.hddcoin/mainnet/config/config.yaml

chmod 755 -R /root/.hddcoin/mainnet/config/ssl/ &> /dev/null
chia init --fix-ssl-permissions > /dev/null 

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
    if [ ! -f /root/.hddcoin/farmer_ca/chia_ca.crt ]; then
      mkdir -p /root/.hddcoin/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${controller_host}:8930/certificates/?type=hddcoin --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.hddcoin/farmer_ca
      else
        echo "Certificates response of ${response} from http://${controller_host}:8930/certificates/?type=hddcoin.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip 
    fi
    if [ -f /root/.hddcoin/farmer_ca/chia_ca.crt ]; then
      chia init -c /root/.hddcoin/farmer_ca 2>&1 > /root/.chia/mainnet/log/init.log
      chmod 755 -R /root/.hddcoin/mainnet/config/ssl/ &> /dev/null
      chia init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.hddcoin/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    chia configure --set-farmer-peer ${farmer_address}:${farmer_port}
    chia configure --enable-upnp false
    chia start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
