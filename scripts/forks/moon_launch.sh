#!/bin/env bash
#
# Initialize Moon service, depending on mode of system requested
#

cd /moon-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store moon within
mkdir -p /root/.chia/moon
rm -f /root/.moon
ln -s /root/.chia/moon /root/.moon 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.moon/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.moon/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  mkdir -p /root/.moon/mainnet/db/ && cd /root/.moon/mainnet/db/
  echo "Sorry, Moon does not offer a recent blockchain DB for download via script.  Standard sync will happen over a few days..."
  echo "It is recommended to add some peer node connections on the Connections page of Machinaris."
fi

mkdir -p /root/.moon/mainnet/log
moon init >> /root/.moon/mainnet/log/init.log 2>&1 

echo 'Configuring Moon...'
if [ -f /root/.moon/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.moon/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.moon/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.moon/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    moon keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    moon plots add -d ${p}
done

#chmod 755 -R /root/.moon/mainnet/config/ssl/ &> /dev/null
#moon init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        moon keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    moon start farmer-no-wallet
  else
    moon start farmer
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.moon/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    moon start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.moon/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.moon/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8953/certificates/?type=moon --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.moon/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8953/certificates/?type=moon.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.moon/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      moon init -c /root/.moon/farmer_ca 2>&1 > /root/.moon/mainnet/log/init.log
      #chmod 755 -R /root/.moon/mainnet/config/ssl/ &> /dev/null
      #moon init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.moon/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    moon configure --set-farmer-peer ${farmer_address}:${farmer_port}
    moon configure --enable-upnp false
    moon start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
