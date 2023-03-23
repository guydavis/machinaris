#!/bin/env bash
#
# Initialize BPX service, depending on mode of system requested
#

cd /bpx-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store bpx within
mkdir -p /root/.chia/bpx
rm -f /root/.bpx
ln -s /root/.chia/bpx /root/.bpx 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.bpx/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.bpx/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  echo "Downloading BPX blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.bpx/mainnet/db/ && cd /root/.bpx/mainnet/db/
  # Download link to blockchain_v2_mainnet.sqlite from their Discord on 2022-10-17
  curl -skJLO https://dbs.ctek.cc/$/6RnzB
fi

mkdir -p /root/.bpx/mainnet/log
bpx init >> /root/.bpx/mainnet/log/init.log 2>&1 

echo 'Configuring BPX...'
if [ -f /root/.bpx/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.bpx/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.bpx/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.bpx/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    bpx keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    bpx plots add -d ${p}
done

chmod 755 -R /root/.bpx/mainnet/config/ssl/ &> /dev/null
bpx init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} =~ ^fullnode.* ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        bpx keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    bpx start farmer-no-wallet
  else
    bpx start farmer
  fi
  if [[ ${mode} =~ .*timelord$ ]]; then
    if [ ! -f vdf_bench ]; then
        echo "Building timelord binaries..."
        apt-get update > /tmp/timelord_build.sh 2>&1 
        apt-get install -y libgmp-dev libboost-python-dev libboost-system-dev >> /tmp/timelord_build.sh 2>&1 
        BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh >> /tmp/timelord_build.sh 2>&1 
    fi
    bpx start timelord-only
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.bpx/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    bpx start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.bpx/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.bpx/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8945/certificates/?type=bpx --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.bpx/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8945/certificates/?type=bpx.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.bpx/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      bpx init -c /root/.bpx/farmer_ca 2>&1 > /root/.bpx/mainnet/log/init.log
      chmod 755 -R /root/.bpx/mainnet/config/ssl/ &> /dev/null
      bpx init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.bpx/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    # This configure command fails, as this blockchain chokes on its own config file!
    bpx configure --set-farmer-peer ${farmer_address}:${farmer_port}  2>&1 >> /root/.bpx/mainnet/log/init.log
    bpx configure --enable-upnp false  2>&1 >> /root/.bpx/mainnet/log/init.log
    # So, perform the configuration into the config.yaml file directly instead...
    sed -z -i "s/  farmer_peer:\n    host: 127.0.0.1\n    port: 18655/  farmer_peer:\n    host: ${farmer_address}\n    port: ${farmer_port}/g" config.yaml
    bpx start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
