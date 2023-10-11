#!/bin/env bash
#
# Initialize BTCGreen service, depending on mode of system requested
#

cd /btcgreen-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store btcgreen within
mkdir -p /root/.chia/btcgreen
rm -f /root/.btcgreen
ln -s /root/.chia/btcgreen /root/.btcgreen 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.btcgreen/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.btcgreen/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  mkdir -p /root/.btcgreen/mainnet/db/ && cd /root/.btcgreen/mainnet/db/
  # Mega links for BTCGreen blockchain DB from their Discord 2022-08-23
  /usr/bin/bash /machinaris/scripts/megacmd_setup.sh > /tmp/megacmd_setup.log 2>&1
  mega-get https://mega.nz/folder/YllTjSYR#S-YDbL6Y98qPpAN81UTs-g
  mv BTCgreen_8_21_22/* . && rm -rf BTCgreen_8_21_22
fi

mkdir -p /root/.btcgreen/mainnet/log
btcgreen init >> /root/.btcgreen/mainnet/log/init.log 2>&1 

echo 'Configuring BTCGreen...'
if [ -f /root/.btcgreen/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.btcgreen/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.btcgreen/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.btcgreen/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
label_num=0
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key #${label_num} at path: ${k}"
    btcgreen keys add -l "key_${label_num}" -f ${k} > /dev/null
    ((label_num=label_num+1))
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    btcgreen plots add -d ${p}
done

chmod 755 -R /root/.btcgreen/mainnet/config/ssl/ &> /dev/null
btcgreen init --fix-ssl-permissions >/dev/null 2>&1   

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} =~ ^fullnode.* ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        btcgreen keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    btcgreen start farmer-no-wallet
  else
    btcgreen start farmer
  fi
  if [[ ${mode} =~ .*timelord$ ]]; then
    if [ ! -f vdf_bench ]; then
        echo "Building timelord binaries..."
        apt-get update > /tmp/timelord_build.sh 2>&1 
        apt-get install -y libgmp-dev libboost-python-dev libboost-system-dev >> /tmp/timelord_build.sh 2>&1 
        BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh >> /tmp/timelord_build.sh 2>&1 
    fi
    btcgreen start timelord-only
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.btcgreen/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    btcgreen start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.btcgreen/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.btcgreen/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8938/certificates/?type=btcgreen --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.btcgreen/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8938/certificates/?type=btcgreen.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.btcgreen/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      btcgreen init -c /root/.btcgreen/farmer_ca 2>&1 > /root/.btcgreen/mainnet/log/init.log
      chmod 755 -R /root/.btcgreen/mainnet/config/ssl/ &> /dev/null
      btcgreen init --fix-ssl-permissions >/dev/null 2>&1   
    else
      echo "Did not find your farmer's certificates within /root/.btcgreen/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}" 
    btcgreen configure --set-farmer-peer ${farmer_address}:${farmer_port}  2>&1 >> /root/.btcgreen/mainnet/log/init.log
    btcgreen configure --enable-upnp false  2>&1 >> /root/.btcgreen/mainnet/log/init.log
    btcgreen start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
