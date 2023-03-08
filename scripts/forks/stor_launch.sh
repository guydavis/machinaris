#!/bin/env bash
#
# Initialize Stor service, depending on mode of system requested
#

cd /stor-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store stor within
mkdir -p /root/.chia/stor
rm -f /root/.stor
ln -s /root/.chia/stor /root/.stor 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.stor/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.stor/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  echo "Downloading Stor blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.stor/mainnet/db/ && cd /root/.stor/mainnet/db/
  # Latest Blockchain DB download from direct from https://eu.stornode.net/
  db_file=$(curl -s https://eu.stornode.net/ | grep -Po 'db-(\d){4}-(\d){2}-(\d){2}'.zip | tail -n 1)
  curl -skJLO https://eu.stornode.net/${db_file}
  unzip db*.zip 
  mv db*/*sqlite .
  rm -rf db*
fi

mkdir -p /root/.stor/mainnet/log
stor init >> /root/.stor/mainnet/log/init.log 2>&1 

echo 'Configuring Stor...'
if [ -f /root/.stor/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.stor/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.stor/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.stor/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    stor keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
  stor plots add -d ${p}
done

chmod 755 -R /root/.stor/mainnet/config/ssl/ &> /dev/null
stor init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} =~ ^fullnode.* ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        stor keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    stor start farmer-no-wallet
  else
    stor start farmer
  fi
  if [[ ${mode} =~ .*timelord$ ]]; then
    if [ ! -f vdf_bench ]; then
        echo "Building timelord binaries..."
        apt-get update > /tmp/timelord_build.sh 2>&1 
        apt-get install -y libgmp-dev libboost-python-dev libboost-system-dev >> /tmp/timelord_build.sh 2>&1 
        BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh >> /tmp/timelord_build.sh 2>&1 
    fi
    stor start timelord-only
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.stor/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    stor start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.stor/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.stor/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8935/certificates/?type=stor --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.stor/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8935/certificates/?type=stor.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.stor/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      stor init -c /root/.stor/farmer_ca 2>&1 > /root/.stor/mainnet/log/init.log
      chmod 755 -R /root/.stor/mainnet/config/ssl/ &> /dev/null
      stor init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.stor/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    stor configure --set-farmer-peer ${farmer_address}:${farmer_port}  2>&1 >> /root/.stor/mainnet/log/init.log
    stor configure --enable-upnp false  2>&1 >> /root/.stor/mainnet/log/init.log
    stor start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
