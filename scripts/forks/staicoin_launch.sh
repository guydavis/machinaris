#!/bin/env bash
#
# Initialize Chia service, depending on mode of system requested
#


cd /staicoin-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store staicoin within
mkdir -p /root/.chia/staicoin
rm -f /root/.staicoin
ln -s /root/.chia/staicoin /root/.staicoin 

mkdir -p /root/.staicoin/mainnet/log
staicoin init >> /root/.staicoin/mainnet/log/init.log 2>&1 

echo 'Configuring Staicoin...'
if [ -f /root/.staicoin/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.staicoin/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.staicoin/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.staicoin/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [ -f ${k} ]; then
    echo "Adding key at path: ${k}"
    staicoin keys add -f ${k} > /dev/null
  else
    echo "Skipping 'staicoin keys add' as no file found at: ${k}"
  fi
done

# Loop over provided list of completed plot directories
for p in ${plots_dir//:/ }; do
    staicoin plots add -d ${p}
done

#chmod 755 -R /root/.staicoin/mainnet/config/ssl/ &> /dev/null
#staicoin init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  if [ ! -f ~/.staicoin/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
    exit 1
  else
    staicoin start farmer
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.staicoin/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    staicoin start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.staicoin/farmer_ca/chia_ca.crt ]; then
      mkdir -p /root/.staicoin/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${controller_host}:8934/certificates/?type=staicoin --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.staicoin/farmer_ca
      else
        echo "Certificates response of ${response} from http://${controller_host}:8934/certificates/?type=staicoin.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip 
    fi
    if [ -f /root/.staicoin/farmer_ca/chia_ca.crt ]; then
      staicoin init -c /root/.staicoin/farmer_ca 2>&1 > /root/.staicoin/mainnet/log/init.log
      #chmod 755 -R /root/.staicoin/mainnet/config/ssl/ &> /dev/null
      #staicoin init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.staicoin/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    staicoin configure --set-farmer-peer ${farmer_address}:${farmer_port}
    staicoin configure --enable-upnp false
    staicoin start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
