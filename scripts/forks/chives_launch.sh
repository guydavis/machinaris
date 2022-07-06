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

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.chives/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.chives/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  /usr/bin/bash /machinaris/scripts/megacmd_setup.sh > /tmp/megacmd_setup.log 2>&1
  echo "Downloading Chives blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.chives/mainnet/db/ && cd /root/.chives/mainnet/db/
  echo "Sorry, Chives does not offer a recent blockchain DB for download.  Standard sync will happen over a few days."
  echo "It is recommended to add some peer node connections on the Connections page of Machinaris from: https://alltheblocks.net/chives"
fi

mkdir -p /root/.chives/mainnet/log
chives init >> /root/.chives/mainnet/log/init.log 2>&1 

echo 'Configuring Chives...'
if [ -f /root/.chives/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.chives/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.chives/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.chives/mainnet/config/config.yaml
fi
# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    chives keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    chives plots add -d ${p}
done

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        chives keys add -f ${k}
        sleep 10
      fi
    done
  done
  chives start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.chives/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
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
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8931/certificates/?type=chives --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.chives/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8931/certificates/?type=chives.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.chives/farmer_ca/chives_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
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
