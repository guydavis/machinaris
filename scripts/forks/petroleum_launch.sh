#!/bin/env bash
#
# Initialize Petroleum service, depending on mode of system requested
#

cd /petroleum-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store petroleum within
mkdir -p /root/.chia/petroleum
rm -f /root/.petroleum
ln -s /root/.chia/petroleum /root/.petroleum 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.petroleum/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.petroleum/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  mkdir -p /root/.petroleum/mainnet/db/ && cd /root/.petroleum/mainnet/db/
  echo "Sorry, Petroleum does not offer a recent blockchain DB for download via script.  Standard sync will happen over a few days..."
  echo "It is recommended to add some peer node connections on the Connections page of Machinaris from: https://alltheblocks.net/petroleum"
fi

mkdir -p /root/.petroleum/mainnet/log
petroleum init >> /root/.petroleum/mainnet/log/init.log 2>&1 

echo 'Configuring Petroleum...'
if [ -f /root/.petroleum/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.petroleum/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.petroleum/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.petroleum/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    petroleum keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    petroleum plots add -d ${p}
done

chmod 755 -R /root/.petroleum/mainnet/config/ssl/ &> /dev/null
petroleum init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        petroleum keys add -f ${k}
        sleep 10
      fi
    done
  done
  petroleum start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.petroleum/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    petroleum start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.petroleum/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.petroleum/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8943/certificates/?type=petroleum --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.petroleum/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8943/certificates/?type=petroleum.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.petroleum/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      petroleum init -c /root/.petroleum/farmer_ca 2>&1 > /root/.petroleum/mainnet/log/init.log
      chmod 755 -R /root/.petroleum/mainnet/config/ssl/ &> /dev/null
      petroleum init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.petroleum/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    petroleum configure --set-farmer-peer ${farmer_address}:${farmer_port}
    petroleum configure --enable-upnp false
    petroleum start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
