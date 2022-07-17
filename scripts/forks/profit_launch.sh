#!/bin/env bash
#
# Initialize Profit service, depending on mode of system requested
#

cd /profit-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store profit within
mkdir -p /root/.chia/profit
rm -f /root/.profit
ln -s /root/.chia/profit /root/.profit 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.profit/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.profit/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  echo "Downloading Profit blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.profit/mainnet/db/ && cd /root/.profit/mainnet/db/
   # Download link from their Discord on 2022-07-07
  gdown 1cH-ub3d--hbYYqrsa3jlNY8vmNWYUavf
  p7zip --decompress --force blockchain_v1_mainnet*.7z
fi

mkdir -p /root/.profit/mainnet/log
profit init >> /root/.profit/mainnet/log/init.log 2>&1 

echo 'Configuring Profit...'
if [ -f /root/.profit/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.profit/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.profit/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.profit/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    profit keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    profit plots add -d ${p}
done

chmod 755 -R /root/.profit/mainnet/config/ssl/ &> /dev/null
profit init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        profit keys add -f ${k}
        sleep 10
      fi
    done
  done
  profit start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.profit/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    profit start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.profit/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.profit/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8944/certificates/?type=profit --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.profit/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8944/certificates/?type=profit.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.profit/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      profit init -c /root/.profit/farmer_ca 2>&1 > /root/.profit/mainnet/log/init.log
      chmod 755 -R /root/.profit/mainnet/config/ssl/ &> /dev/null
      profit init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.profit/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    profit configure --set-farmer-peer ${farmer_address}:${farmer_port}
    profit configure --enable-upnp false
    profit start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
