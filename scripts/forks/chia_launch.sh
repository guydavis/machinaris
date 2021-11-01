#!/bin/env bash
#
# Initialize Chia service, depending on mode of system requested
#


cd /chia-blockchain

. ./activate

mkdir -p /root/.chia/mainnet/log
chia init >> /root/.chia/mainnet/log/init.log 2>&1 

if [[ ! -z "${blockchain_skip_download}" ]] && [[! -f /root/.chia/mainnet/db/blockchain_v1_mainnet.sqlite ]]; then
  echo "Downloading Chia blockchain DB on first launch..."
  mkdir -p /root/.chia/mainnet/db/ && cd /root/.chia/mainnet/db/
  # Mega links for Chia blockchain DB from: https://chiaforksblockchain.com/
  mega-get https://mega.nz/folder/eQIhCSjD#PcfxQS0QZUSU9lQgwmmlqA/file/nVBURRLT
  mega-get https://mega.nz/folder/eQIhCSjD#PcfxQS0QZUSU9lQgwmmlqA/file/uZJQTJZb
fi

echo 'Configuring Chia...'
if [ ! -f /root/.chia/mainnet/config/config.yaml ]; then
  sleep 10
fi
if [ -f /root/.chia/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.chia/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.chia/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.chia/mainnet/config/config.yaml
fi

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

chmod 755 -R /root/.chia/mainnet/config/ssl/ &> /dev/null
chia init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  chia start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  chia start farmer-only
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit 1
  else
    if [ ! -f /root/.chia/farmer_ca/chia_ca.crt ]; then
      mkdir -p /root/.chia/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${controller_host}:8927/certificates/?type=chia --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.chia/farmer_ca
      else
        echo "Certificates response of ${response} from http://${controller_host}:8927/certificates/?type=chia.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip 
    fi
    if [ -f /root/.chia/farmer_ca/chia_ca.crt ]; then
      chia init -c /root/.chia/farmer_ca 2>&1 > /root/.chia/mainnet/log/init.log
      chmod 755 -R /root/.chia/mainnet/config/ssl/ &> /dev/null
      chia init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.chia/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    chia configure --set-farmer-peer ${farmer_address}:${farmer_port}
    chia configure --enable-upnp false
    chia start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
