#!/bin/env bash
#
# Initialize Wheat service, depending on mode of system requested
#

cd /wheat-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store wheat within
mkdir -p /root/.chia/wheat
rm -f /root/.wheat
ln -s /root/.chia/wheat /root/.wheat 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.wheat/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.wheat/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  echo "Sorry, Wheat does not offer a recent blockchain DB for download.  Standard sync will happen over a few days."
  echo "It is recommended to add some peer node connections on the Connections page of Machinaris."
fi

mkdir -p /root/.wheat/mainnet/log
wheat init >> /root/.wheat/mainnet/log/init.log 2>&1 

echo 'Configuring Wheat...'
if [ -f /root/.wheat/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.wheat/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.wheat/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.wheat/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
label_num=0
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key #${label_num} at path: ${k}"
    wheat keys add -l "key_${label_num}" -f ${k} > /dev/null
    ((label_num=label_num+1))
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    wheat plots add -d ${p}
done

chmod 755 -R /root/.wheat/mainnet/config/ssl/ &> /dev/null
wheat init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} =~ ^fullnode.* ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        wheat keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    wheat start farmer-no-wallet
  else
    wheat start farmer
  fi
  if [[ ${mode} =~ .*timelord$ ]]; then
    if [ ! -f vdf_bench ]; then
        echo "Building timelord binaries..."
        apt-get update > /tmp/timelord_build.sh 2>&1 
        apt-get install -y libgmp-dev libboost-python-dev libboost-system-dev >> /tmp/timelord_build.sh 2>&1 
        BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh >> /tmp/timelord_build.sh 2>&1 
    fi
    wheat start timelord-only
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.wheat/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    wheat start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.wheat/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.wheat/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8952/certificates/?type=wheat --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.wheat/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8952/certificates/?type=wheat.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.wheat/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      wheat init -c /root/.wheat/farmer_ca 2>&1 > /root/.wheat/mainnet/log/init.log
      chmod 755 -R /root/.wheat/mainnet/config/ssl/ &> /dev/null
      wheat init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.wheat/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    wheat configure --set-farmer-peer ${farmer_address}:${farmer_port}  2>&1 >> /root/.wheat/mainnet/log/init.log
    wheat configure --enable-upnp false  2>&1 >> /root/.wheat/mainnet/log/init.log
    wheat start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
