#!/bin/env bash
#
# Initialize Flora service, depending on mode of system requested
#

cd /flora-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store flora within
mkdir -p /root/.chia/flora
rm -f /root/.flora
ln -s /root/.chia/flora /root/.flora 

mkdir -p /root/.flora/mainnet/log
flora init >> /root/.flora/mainnet/log/init.log 2>&1 

echo 'Configuring Flora...'
while [ ! -f /root/.flora/mainnet/config/config.yaml ]; do
  echo "Waiting for creation of /root/.flora/mainnet/config/config.yaml..."
  sleep 1
done
sed -i 's/log_stdout: true/log_stdout: false/g' /root/.flora/mainnet/config/config.yaml
sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.flora/mainnet/config/config.yaml

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [ -f ${k} ]; then
    echo "Adding key at path: ${k}"
    flora keys add -f ${k} > /dev/null
  else
    echo "Skipping 'flora keys add' as no file found at: ${k}"
  fi
done

# Loop over provided list of completed plot directories
if [ -z "${flora_plots_dir}" ]; then
  for p in ${plots_dir//:/ }; do
    flora plots add -d ${p}
  done
else
  for p in ${flora_plots_dir//:/ }; do
    flora plots add -d ${p}
  done
fi

sed -i 's/localhost/127.0.0.1/g' ~/.flora/mainnet/config/config.yaml

chmod 755 -R /root/.flora/mainnet/config/ssl/ &> /dev/null
flora init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  if [ ! -f ~/.flora/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your mnemonic.txt to /root/.chia and restart."
  else
    flora start farmer
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.flora/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your mnemonic.txt to /root/.chia and restart."
  else
    flora start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.flora/farmer_ca/flora_ca.crt ]; then
      mkdir -p /root/.flora/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${controller_host}:8932/certificates/?type=flora --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.flora/farmer_ca
      else
        echo "Certificates response of ${response} from http://${controller_host}:8932/certificates/?type=flora.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip 
    fi
    if [ -f /root/.flora/farmer_ca/flora_ca.crt ]; then
      flora init -c /root/.flora/farmer_ca 2>&1 > /root/.flora/mainnet/log/init.log
      chmod 755 -R /root/.flora/mainnet/config/ssl/ &> /dev/null
      flora init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.flora/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    flora configure --set-farmer-peer ${farmer_address}:${farmer_port}
    flora configure --enable-upnp false
    flora start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
