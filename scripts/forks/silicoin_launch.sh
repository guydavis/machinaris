#!/bin/env bash
#
# Initialize Silicoin service, depending on mode of system requested
#

cd /silicoin-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store sit within
mkdir -p /root/.chia/sit
rm -f /root/.sit
ln -s /root/.chia/sit /root/.sit 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.sit/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.sit/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  mkdir -p /root/.sit/mainnet/db/ && cd /root/.sit/mainnet/db/
  echo "Sorry, Silicoin does not offer a recent blockchain DB for download via script.  Standard sync will happen over a few weeks."
  echo "It is recommended to add some peer node connections on the Connections page of Machinaris."
fi

mkdir -p /root/.sit/mainnet/log
sit init >> /root/.sit/mainnet/log/init.log 2>&1 

echo 'Configuring Silicoin...'
if [ -f /root/.sit/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.sit/mainnet/config/config.yaml
  # Fix port conflicts with other blockchains
  sed -i 's/11000/22000/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/11222/22222/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/11256/22256/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/11445/22445/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/11446/22446/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/11447/22447/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/11448/22448/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/11449/22449/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/11555/22555/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/11559/22559/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/11560/22560/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/12444/22444/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/21234/22234/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/22222/22222/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/: 514/: 22514/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/56400/22400/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/56402/22402/g' /root/.sit/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    sit keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    sit plots add -d ${p}
done

chmod 755 -R /root/.sit/mainnet/config/ssl/ &> /dev/null
sit init --fix-ssl-permissions 2>&1  >/dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} =~ ^fullnode.* ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        sit keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    sit start farmer-no-wallet
  else
    sit start farmer
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.sit/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    sit start farmer-only
  fi
  if [[ ${mode} =~ .*timelord$ ]]; then
    if [ ! -f vdf_bench ]; then
        echo "Building timelord binaries..."
        apt-get update > /tmp/timelord_build.sh 2>&1 
        apt-get install -y libgmp-dev libboost-python-dev libboost-system-dev >> /tmp/timelord_build.sh 2>&1 
        BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh >> /tmp/timelord_build.sh 2>&1 
    fi
    sit start timelord-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.sit/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.sit/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8941/certificates/?type=silicoin --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.sit/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8941/certificates/?type=silicoin.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.sit/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      sit init -c /root/.sit/farmer_ca 2>&1 > /root/.sit/mainnet/log/init.log
      chmod 755 -R /root/.sit/mainnet/config/ssl/ &> /dev/null
      sit init --fix-ssl-permissions 2>&1  >/dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.sit/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    sit configure --set-farmer-peer ${farmer_address}:${farmer_port}  2>&1 >> /root/.sit/mainnet/log/init.log
    sit configure --enable-upnp false  2>&1 >> /root/.sit/mainnet/log/init.log
    sit start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
