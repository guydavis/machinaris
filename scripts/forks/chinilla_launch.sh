#!/bin/env bash
#
# Initialize Chinilla service, depending on mode of system requested
#

cd /chinilla-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store chinilla within
mkdir -p /root/.chia/chinilla
rm -f /root/.chinilla
ln -s /root/.chia/chinilla /root/.chinilla 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.chinilla/vanillanet/db/blockchain_v1_vanillanet.sqlite ]] \
  && [[ ! -f /root/.chinilla/vanillanet/db/blockchain_v2_vanillanet.sqlite ]]; then
  echo "Sorry, Chinilla does not offer a recent blockchain DB for download.  Standard sync will happen over a few days."
  echo "It is recommended to add some peer node connections on the Connections page of Machinaris from: https://alltheblocks.net/chinilla"
fi

mkdir -p /root/.chinilla/vanillanet/log
chinilla init >> /root/.chinilla/vanillanet/log/init.log 2>&1 

echo 'Configuring Chinilla...'
if [ -f /root/.chinilla/vanillanet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.chinilla/vanillanet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.chinilla/vanillanet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.chinilla/vanillanet/config/config.yaml
fi

# Loop over provided list of key paths
label_num=0
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key #${label_num} at path: ${k}"
    chinilla keys add -l "key_${label_num}" -f ${k} > /dev/null
    ((label_num=label_num+1))
  elif [[ ${mode} == 'fullnode' ]]; then
    echo "Skipping 'chinilla keys add' as no file found at: ${k}"
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    chinilla plots add -d ${p}
done

chmod 755 -R /root/.chinilla/vanillanet/config/ssl/ &> /dev/null
chinilla init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        chinilla keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    chinilla start farmer-no-wallet
  else
    chinilla start farmer
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.chinilla/vanillanet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    chinilla start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.chinilla/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.chinilla/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8948/certificates/?type=chinilla --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.chinilla/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8948/certificates/?type=chinilla.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.chinilla/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      chinilla init -c /root/.chinilla/farmer_ca 2>&1 > /root/.chinilla/vanillanet/log/init.log
      chmod 755 -R /root/.chinilla/vanillanet/config/ssl/ &> /dev/null
      chinilla init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.chinilla/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    chinilla configure --set-farmer-peer ${farmer_address}:${farmer_port}
    chinilla configure --enable-upnp false
    chinilla start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
