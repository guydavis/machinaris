#!/bin/env bash
#
# Initialize Chia service, depending on mode of system requested
#


cd /hddcoin-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store hddcoin within
mkdir -p /root/.chia/hddcoin
rm -f /root/.hddcoin
ln -s /root/.chia/hddcoin /root/.hddcoin

mkdir -p /root/.hddcoin/mainnet/log
hddcoin init >> /root/.hddcoin/mainnet/log/init.log 2>&1

if [[ ! -z "${blockchain_db_download}" ]] && [[ "${mode}" == 'fullnode' ]] && [[ ! -f /root/.hddcoin/mainnet/db/blockchain_v1_mainnet.sqlite ]]; then
  echo "Downloading HDDCoin blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.hddcoin/mainnet/db/ && cd /root/.hddcoin/mainnet/db/
  # Mega links for HDDCoin blockchain DB from: https://chiaforksblockchain.com/
  mega-get https://mega.nz/folder/6IpSyDBJ#NbGmW1GuV_JXzqzki8TbeA
  mv hddcoin/*.sqlite . && rm -rf hddcoin
fi

echo 'Configuring HDDCoin...'
if [ -f /root/.hddcoin/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.hddcoin/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.hddcoin/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.hddcoin/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key at path: ${k}"
    hddcoin keys add -f ${k} > /dev/null
  fi
done

# Loop over provided list of completed plot directories
for p in ${plots_dir//:/ }; do
    hddcoin plots add -d ${p}
done

chmod 755 -R /root/.hddcoin/mainnet/config/ssl/ &> /dev/null
hddcoin init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        hddcoin keys add -f ${k}
        sleep 10
      fi
    done
  done
  hddcoin start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.hddcoin/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    hddcoin start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.hddcoin/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.hddcoin/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${controller_host}:8930/certificates/?type=hddcoin --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.hddcoin/farmer_ca
      else
        echo "Certificates response of ${response} from http://${controller_host}:8930/certificates/?type=hddcoin.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip 
    fi
    if [ -f /root/.hddcoin/farmer_ca/private_ca.crt ]; then
      hddcoin init -c /root/.hddcoin/farmer_ca 2>&1 > /root/.hddcoin/mainnet/log/init.log
      chmod 755 -R /root/.hddcoin/mainnet/config/ssl/ &> /dev/null
      hddcoin init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.hddcoin/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    hddcoin configure --set-farmer-peer ${farmer_address}:${farmer_port}
    hddcoin configure --enable-upnp false
    hddcoin start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
