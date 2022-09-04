#!/bin/env bash
#
# Initialize Gold service, depending on mode of system requested
#

cd /gold-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store gold within
mkdir -p /root/.chia/gold
rm -f /root/.gold
ln -s /root/.chia/gold /root/.gold 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.gold/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.gold/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  echo "Downloading Gold blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.gold/mainnet/db/ && cd /root/.gold/mainnet/db/
  # Latest Blockchain DB download as per the Gold Discord
  curl -skJLO http://58.7.212.211/C%3A/http/Gold/951456/Gold.blockchain_v1_mainnet.height.951456.db.rar
  unrar e *.rar 
  rm -f *.rar
fi

mkdir -p /root/.gold/mainnet/log
gold init >> /root/.gold/mainnet/log/init.log 2>&1 

echo 'Configuring Gold...'
if [ -f /root/.gold/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.gold/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.gold/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.gold/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    gold keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    gold plots add -d ${p}
done

chmod 755 -R /root/.gold/mainnet/config/ssl/ &> /dev/null
gold init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        gold keys add -f ${k}
        sleep 10
      fi
    done
  done
  gold start farmer-no-wallet
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.gold/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    gold start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.gold/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.gold/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8949/certificates/?type=gold --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.gold/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8949/certificates/?type=gold.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.gold/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      gold init -c /root/.gold/farmer_ca 2>&1 > /root/.gold/mainnet/log/init.log
      chmod 755 -R /root/.gold/mainnet/config/ssl/ &> /dev/null
      gold init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.gold/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    gold configure --set-farmer-peer ${farmer_address}:${farmer_port}
    gold configure --enable-upnp false
    gold start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
