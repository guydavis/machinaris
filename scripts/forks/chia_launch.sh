#!/bin/env bash
#
# Initialize Chia service, depending on mode of system requested
#

# Ensure Chia keyring is held on a persistent volume
mkdir -p /root/.chia/.chia_keys
rm -f /root/.chia_keys
ln -s /root/.chia/.chia_keys /root/.chia_keys

cd /chia-blockchain

. ./activate

mkdir -p /root/.chia/mainnet/log
chia init >> /root/.chia/mainnet/log/init.log 2>&1 

if [[ -z "${blockchain_skip_download}" ]] && [[ "${mode}" == 'fullnode' ]] && [[ ! -f /root/.chia/mainnet/db/blockchain_v1_mainnet.sqlite ]]; then
  # Create machinaris dbs and launch web only while blockchain database downloads
  . /machinaris/scripts/setup_databases.sh
  mkdir -p /root/.chia/machinaris/config
  mkdir -p /root/.chia/machinaris/logs
  cd /machinaris
  /chia-blockchain/venv/bin/gunicorn \
      --bind 0.0.0.0:8926 --timeout 90 \
      --log-level=info \
      --workers=2 \
      --log-config web/log.conf \
      web:app &
  echo 'Starting web server...  Browse to port 8926.'
  echo "Downloading Chia blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.chia/mainnet/db/ && cd /root/.chia/mainnet/db/
  # Mega links for Chia blockchain DB from: https://chiaforksblockchain.com/
  mega-get https://mega.nz/folder/eQIhCSjD#PcfxQS0QZUSU9lQgwmmlqA
  mv chia/*.sqlite . && rm -rf chia
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
