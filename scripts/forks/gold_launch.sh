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
  /usr/bin/bash /machinaris/scripts/megacmd_setup.sh > /tmp/megacmd_setup.log 2>&1
  mkdir -p /root/.gold/mainnet/db/ && cd /root/.gold/mainnet/db/
  # Mega links for Gold blockchain DB from their Discord 2022-10-24
  mega-get https://mega.nz/folder/XAhB1bbC#vvlz5NKwtL0iS_WXGsVg2w
  cd db/ && unrar e "db-$(date +'%Y-%m-%d').rar" && mv *.sqlite ../
  cd ../ && rm -rf db
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
if [[ ${mode} =~ ^fullnode.* ]]; then
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
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    gold start farmer-no-wallet
  else
    gold start farmer
  fi
  if [[ ${mode} =~ .*timelord$ ]]; then
    if [ ! -f vdf_bench ]; then
        echo "Building timelord binaries..."
        apt-get update > /tmp/timelord_build.sh 2>&1 
        apt-get install -y libgmp-dev libboost-python-dev libboost-system-dev >> /tmp/timelord_build.sh 2>&1 
        BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh >> /tmp/timelord_build.sh 2>&1 
    fi
    gold start timelord-only
  fi
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
    gold configure --set-farmer-peer ${farmer_address}:${farmer_port}  2>&1 >> /root/.gold/mainnet/log/init.log
    gold configure --enable-upnp false  2>&1 >> /root/.gold/mainnet/log/init.log
    gold start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
