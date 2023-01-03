#!/bin/env bash
#
# Initialize Coffee service, depending on mode of system requested
#

cd /coffee-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store coffee within
mkdir -p /root/.chia/coffee
rm -f /root/.coffee
ln -s /root/.chia/coffee /root/.coffee 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.coffee/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.coffee/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  echo "Sorry, Coffee does not offer a recent blockchain DB for download.  Standard sync will happen over a few weeks."
  echo "It is recommended to add some peer node connections on the Connections page of Machinaris."
fi

mkdir -p /root/.coffee/mainnet/log
coffee init >> /root/.coffee/mainnet/log/init.log 2>&1 

echo 'Configuring Coffee...'
if [ -f /root/.coffee/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.coffee/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.coffee/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.coffee/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    coffee keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    coffee plots add -d ${p}
done

chmod 755 -R /root/.coffee/mainnet/config/ssl/ &> /dev/null
coffee init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        coffee keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    coffee start farmer-no-wallet
  else
    coffee start farmer
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.coffee/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    coffee start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.coffee/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.coffee/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8954/certificates/?type=coffee --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.coffee/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8954/certificates/?type=coffee.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.coffee/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      coffee init -c /root/.coffee/farmer_ca 2>&1 > /root/.coffee/mainnet/log/init.log
      chmod 755 -R /root/.coffee/mainnet/config/ssl/ &> /dev/null
      coffee init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.coffee/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    coffee configure --set-farmer-peer ${farmer_address}:${farmer_port}
    coffee configure --enable-upnp false
    coffee start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
