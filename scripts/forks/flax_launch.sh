#!/bin/env bash
#
# Initialize Flax service, depending on mode of system requested
#

cd /flax-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store flax within
mkdir -p /root/.chia/flax
rm -f /root/.flax
ln -s /root/.chia/flax /root/.flax 

mkdir -p /root/.flax/mainnet/log
flax init >> /root/.flax/mainnet/log/init.log 2>&1 

echo 'Configuring Flax...'
while [ ! -f /root/.flax/mainnet/config/config.yaml ]; do
  echo "Waiting for creation of /root/.flax/mainnet/config/config.yaml..."
  sleep 1
done
sed -i 's/log_stdout: true/log_stdout: false/g' /root/.flax/mainnet/config/config.yaml
sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.flax/mainnet/config/config.yaml

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  if [ -f ${k} ]; then
    echo "Adding key at path: ${k}"
    flax keys add -f ${k} > /dev/null
  else
    echo "Skipping 'flax keys add' as no file found at: ${k}"
  fi
done

# Loop over provided list of completed plot directories
if [ -z "${flax_plots_dir}" ]; then
  for p in ${plots_dir//:/ }; do
    flax plots add -d ${p}
  done
else
  for p in ${flax_plots_dir//:/ }; do
    flax plots add -d ${p}
  done
fi

sed -i 's/localhost/127.0.0.1/g' ~/.flax/mainnet/config/config.yaml

chmod 755 -R /root/.flax/mainnet/config/ssl/ &> /dev/null
flax init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  if [ ! -f ~/.flax/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your mnemonic.txt to /root/.chia and restart."
  else
    flax start farmer
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.flax/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your mnemonic.txt to /root/.chia and restart."
  else
    flax start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.flax/farmer_ca/flax_ca.crt ]; then
      mkdir -p /root/.flax/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${controller_host}:8928/certificates/?type=flax --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.flax/farmer_ca
      else
        echo "Certificates response of ${response} from http://${controller_host}:8928/certificates/?type=flax.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip 
    fi
    if [ -f /root/.flax/farmer_ca/flax_ca.crt ]; then
      flax init -c /root/.flax/farmer_ca 2>&1 > /root/.flax/mainnet/log/init.log
      chmod 755 -R /root/.flax/mainnet/config/ssl/ &> /dev/null
      flax init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.flax/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    flax configure --set-farmer-peer ${farmer_address}:${farmer_port}
    flax configure --enable-upnp false
    flax start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
