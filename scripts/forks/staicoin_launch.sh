#!/bin/env bash
#
# Initialize Staicoin service, depending on mode of system requested
#

cd /staicoin-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store staicoin within
mkdir -p /root/.chia/staicoin
rm -f /root/.staicoin
ln -s /root/.chia/staicoin /root/.staicoin 
rm -f /root/.stai
ln -s /root/.chia/staicoin /root/.stai

mkdir -p /root/.staicoin/mainnet/log
stai init >> /root/.staicoin/mainnet/log/init.log 2>&1 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ -f /usr/bin/mega-get ]] \
  && [[ ! -f /root/.staicoin/mainnet/db/blockchain_v1_mainnet.sqlite ]]; then
  echo "Downloading Staicoin blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.staicoin/mainnet/db/ && cd /root/.staicoin/mainnet/db/
  # Mega links for Staicoin blockchain DB from: https://chiaforksblockchain.com/
  mega-get https://mega.nz/folder/OqgSjYCY#MCwYdt3YnnHA2C6gJV6lvw
  mv staicoin/*.sqlite . && rm -rf staicoin
fi

echo 'Configuring Staicoin...'
if [ -f /root/.staicoin/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.staicoin/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.staicoin/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.staicoin/mainnet/config/config.yaml
  # Fix for their renaming from staicoin to stai in December 2021
  sed -i 's/staicoin_ssl_ca/stai_ssl_ca/g' /root/.staicoin/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    stai keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
for p in ${plots_dir//:/ }; do
    stai plots add -d ${p}
done

chmod 755 -R /root/.staicoin/mainnet/config/ssl/ &> /dev/null
stai init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        stai keys add -f ${k}
        sleep 10
      fi
    done
  done
  stai start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.staicoin/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    stai start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.staicoin/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.staicoin/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8934/certificates/?type=stai --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.staicoin/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8934/certificates/?type=staicoin.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip 
    fi
    if [ -f /root/.staicoin/farmer_ca/private_ca.crt ]; then
      stai init -c /root/.staicoin/farmer_ca 2>&1 > /root/.staicoin/mainnet/log/init.log
      chmod 755 -R /root/.staicoin/mainnet/config/ssl/ &> /dev/null
      stai init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.staicoin/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    stai configure --set-farmer-peer ${farmer_address}:${farmer_port}
    stai configure --enable-upnp false
    stai start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
