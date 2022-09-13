#!/bin/env bash
#
# Initialize LittleLamboCoin service, depending on mode of system requested
#

cd /littlelambocoin-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store littlelambocoin within
mkdir -p /root/.chia/littlelambocoin
rm -f /root/.littlelambocoin
ln -s /root/.chia/littlelambocoin /root/.littlelambocoin 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.littlelambocoin/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.littlelambocoin/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  echo "Downloading LittleLamboCoin blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  /usr/bin/bash /machinaris/scripts/megacmd_setup.sh > /tmp/megacmd_setup.log 2>&1
  mkdir -p /root/.littlelambocoin/mainnet/db/ && cd /root/.littlelambocoin/mainnet/db/
  # Mega links for LLC blockchain DB from their Discord 2022-08-20
  mega-get https://mega.nz/file/zogiGLqa#Ui6ONP7prArhrTDAOIYPrTejZ2gM5Mk8kb7rocniwKQ
  #mv llc_v2/* . && rm -rf llc_v2
fi

mkdir -p /root/.littlelambocoin/mainnet/log
littlelambocoin init >> /root/.littlelambocoin/mainnet/log/init.log 2>&1 

echo 'Configuring LittleLamboCoin...'
if [ -f /root/.littlelambocoin/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.littlelambocoin/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.littlelambocoin/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.littlelambocoin/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    littlelambocoin keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    littlelambocoin plots add -d ${p}
done

chmod 755 -R /root/.littlelambocoin/mainnet/config/ssl/ &> /dev/null
littlelambocoin init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        littlelambocoin keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    littlelambocoin start farmer-no-wallet
  else
    littlelambocoin start farmer
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.littlelambocoin/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    littlelambocoin start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.littlelambocoin/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.littlelambocoin/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8946/certificates/?type=littlelambocoin --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.littlelambocoin/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8946/certificates/?type=littlelambocoin.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.littlelambocoin/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      littlelambocoin init -c /root/.littlelambocoin/farmer_ca 2>&1 > /root/.littlelambocoin/mainnet/log/init.log
      chmod 755 -R /root/.littlelambocoin/mainnet/config/ssl/ &> /dev/null
      littlelambocoin init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.littlelambocoin/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    # This configure command fails, as this blockchain chokes on its own config file!
    littlelambocoin configure --set-farmer-peer ${farmer_address}:${farmer_port}
    littlelambocoin configure --enable-upnp false
    # So, perform the configuration into the config.yaml file directly instead...
    sed -z -i "s/  farmer_peer:\n    host: 127.0.0.1\n    port: 18714/  farmer_peer:\n    host: ${farmer_address}\n    port: ${farmer_port}/g" config.yaml
    littlelambocoin start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
