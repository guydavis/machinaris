#!/bin/env bash
#
# Initialize Ecostake service, depending on mode of system requested
#

cd /ecostake-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store ecostake within
mkdir -p /root/.chia/ecostake
rm -f /root/.ecostake
ln -s /root/.chia/ecostake /root/.ecostake 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.ecostake/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.ecostake/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  echo "Sorry, Ecostake does not offer a recent blockchain DB for download.  Standard sync will happen over a few weeks."
  echo "It is recommended to add some peer node connections on the Connections page of Machinaris."
fi

mkdir -p /root/.ecostake/mainnet/log
ecostake init >> /root/.ecostake/mainnet/log/init.log 2>&1 

echo 'Configuring Ecostake...'
if [ -f /root/.ecostake/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.ecostake/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.ecostake/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.ecostake/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    ecostake keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    ecostake plots add -d ${p}
done

chmod 755 -R /root/.ecostake/mainnet/config/ssl/ &> /dev/null
ecostake init --fix-ssl-permissions 2>&1  >/dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} =~ ^fullnode.* ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        ecostake keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    ecostake start farmer-no-wallet
  else
    ecostake start farmer
  fi
  if [[ ${mode} =~ .*timelord$ ]]; then
    if [ ! -f vdf_bench ]; then
        echo "Building timelord binaries..."
        apt-get update > /tmp/timelord_build.sh 2>&1 
        apt-get install -y libgmp-dev libboost-python-dev libboost-system-dev >> /tmp/timelord_build.sh 2>&1 
        BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh >> /tmp/timelord_build.sh 2>&1 
    fi
    ecostake start timelord-only
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.ecostake/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    ecostake start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.ecostake/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.ecostake/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8942/certificates/?type=ecostake --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.ecostake/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8942/certificates/?type=ecostake.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.ecostake/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      ecostake init -c /root/.ecostake/farmer_ca 2>&1 > /root/.ecostake/mainnet/log/init.log
      chmod 755 -R /root/.ecostake/mainnet/config/ssl/ &> /dev/null
      ecostake init --fix-ssl-permissions 2>&1  >/dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.ecostake/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    ecostake configure --set-farmer-peer ${farmer_address}:${farmer_port}  2>&1 >> /root/.ecostake/mainnet/log/init.log
    ecostake configure --enable-upnp false  2>&1 >> /root/.ecostake/mainnet/log/init.log
    ecostake start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
