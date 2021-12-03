#!/bin/env bash
#
# Initialize Cryptodoge service, depending on mode of system requested
#

cd /cryptodoge-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so cryptodogee cryptodoge within
mkdir -p /root/.chia/cryptodoge
rm -f /root/.cryptodoge
ln -s /root/.chia/cryptodoge /root/.cryptodoge 

mkdir -p /root/.cryptodoge/mainnet/log
cryptodoge init >> /root/.cryptodoge/mainnet/log/init.log 2>&1 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ -f /usr/bin/mega-get ]] \
  && [[ ! -f /root/.cryptodoge/mainnet/db/blockchain_v1_mainnet.sqlite ]]; then
  echo "Downloading Cryptodoge blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.cryptodoge/mainnet/db/ && cd /root/.cryptodoge/mainnet/db/
  # Mega links for Cryptodoge blockchain DB from: https://chiaforksblockchain.com/
  mega-get https://mega.nz/folder/T75UDKpA#dLVq8OhdsjK5kPxNwCaP8Q
  mv cryptodoge/*.sqlite . && rm -rf cryptodoge
fi

echo 'Configuring Cryptodoge...'
if [ -f /root/.cryptodoge/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.cryptodoge/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.cryptodoge/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.cryptodoge/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    cryptodoge keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
for p in ${plots_dir//:/ }; do
  cryptodoge plots add -d ${p}
done

chmod 755 -R /root/.cryptodoge/mainnet/config/ssl/ &> /dev/null
cryptodoge init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        cryptodoge keys add -f ${k}
        sleep 10
      fi
    done
  done
  cryptodoge start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.cryptodoge/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    cryptodoge start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.cryptodoge/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.cryptodoge/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8937/certificates/?type=cryptodoge --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.cryptodoge/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8937/certificates/?type=cryptodoge.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip 
    fi
    if [ -f /root/.cryptodoge/farmer_ca/private_ca.crt ]; then
      cryptodoge init -c /root/.cryptodoge/farmer_ca 2>&1 > /root/.cryptodoge/mainnet/log/init.log
      chmod 755 -R /root/.cryptodoge/mainnet/config/ssl/ &> /dev/null
      cryptodoge init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.cryptodoge/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    cryptodoge configure --set-farmer-peer ${farmer_address}:${farmer_port}
    cryptodoge configure --enable-upnp false
    cryptodoge start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
