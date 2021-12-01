#!/bin/env bash
#
# Initialize Maize service, depending on mode of system requested
#

cd /maize-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store maize within
mkdir -p /root/.chia/maize
rm -f /root/.maize
ln -s /root/.chia/maize /root/.maize 

mkdir -p /root/.maize/mainnet/log
maize init >> /root/.maize/mainnet/log/init.log 2>&1 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ -f /usr/bin/mega-get ]] \
  && [[ ! -f /root/.maize/mainnet/db/blockchain_v1_mainnet.sqlite ]]; then
  echo "Downloading Maize blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.maize/mainnet/db/ && cd /root/.maize/mainnet/db/
  # Mega links for Maize blockchain DB from: https://chiaforksblockchain.com/
  mega-get https://mega.nz/folder/KIwkDbjY#wcU3oKyhS3GZiwNbv4UQUA
  mv maize/*mainnet.sqlite maize/*node.sqlite . && rm -rf maize
fi

echo 'Configuring Maize...'
if [ -f /root/.maize/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.maize/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.maize/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.maize/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    maize keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
for p in ${plots_dir//:/ }; do
    maize plots add -d ${p}
done

#chmod 755 -R /root/.maize/mainnet/config/ssl/ &> /dev/null
#maize init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        maize keys add -f ${k}
        sleep 10
      fi
    done
  done
  maize start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.maize/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    maize start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.maize/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.maize/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8933/certificates/?type=maize --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.maize/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8933/certificates/?type=maize.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip 
    fi
    if [ -f /root/.maize/farmer_ca/private_ca.crt ]; then
      maize init -c /root/.maize/farmer_ca 2>&1 > /root/.maize/mainnet/log/init.log
      #chmod 755 -R /root/.maize/mainnet/config/ssl/ &> /dev/null
      #maize init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.maize/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    maize configure --set-farmer-peer ${farmer_address}:${farmer_port}
    maize configure --enable-upnp false
    maize start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
