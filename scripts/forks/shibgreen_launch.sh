#!/bin/env bash
#
# Initialize SHIBGreen service, depending on mode of system requested
#

cd /shibgreen-blockchain

. ./activate

# Only the /root/.chia folder is volume-mounted so store shibgreen within
mkdir -p /root/.chia/shibgreen
rm -f /root/.shibgreen
ln -s /root/.chia/shibgreen /root/.shibgreen 

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.shibgreen/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.shibgreen/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  mkdir -p /root/.shibgreen/mainnet/db/ && cd /root/.shibgreen/mainnet/db/
  # Mega links for SHIBGreen blockchain DB from their Discord 2022-08-23
  /usr/bin/bash /machinaris/scripts/megacmd_setup.sh > /tmp/megacmd_setup.log 2>&1
  mega-get https://mega.nz/folder/QpU3UbgQ#J76hG6GE5cYioiLyCweV1w
  mv shibgreen_8_21_22/* . && rm -rf shibgreen_8_21_22
fi

mkdir -p /root/.shibgreen/mainnet/log
shibgreen init >> /root/.shibgreen/mainnet/log/init.log 2>&1 

echo 'Configuring SHIBGreen...'
if [ -f /root/.shibgreen/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.shibgreen/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.shibgreen/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.shibgreen/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
label_num=0
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key #${label_num} at path: ${k}"
    shibgreen keys add -l "key_${label_num}" -f ${k} > /dev/null
    ((label_num=label_num+1))
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    shibgreen plots add -d ${p}
done

chmod 755 -R /root/.shibgreen/mainnet/config/ssl/ &> /dev/null
shibgreen init --fix-ssl-permissions > /dev/null 

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} =~ ^fullnode.* ]]; then
  for k in ${keys//:/ }; do
    while [[ "${k}" != "persistent" ]] && [[ ! -s ${k} ]]; do
      echo 'Waiting for key to be created/imported into mnemonic.txt. See: http://localhost:8926'
      sleep 10  # Wait 10 seconds before checking for mnemonic.txt presence
      if [ -s ${k} ]; then
        shibgreen keys add -f ${k}
        sleep 10
      fi
    done
  done
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    shibgreen start farmer-no-wallet
  else
    shibgreen start farmer
  fi
  if [[ ${mode} =~ .*timelord$ ]]; then
    if [ ! -f vdf_bench ]; then
        echo "Building timelord binaries..."
        apt-get update > /tmp/timelord_build.sh 2>&1 
        apt-get install -y libgmp-dev libboost-python-dev libboost-system-dev >> /tmp/timelord_build.sh 2>&1 
        BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh >> /tmp/timelord_build.sh 2>&1 
    fi
    shibgreen start timelord-only
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  if [ ! -f ~/.shibgreen/mainnet/config/ssl/wallet/public_wallet.key ]; then
    echo "No wallet key found, so not starting farming services.  Please add your Chia mnemonic.txt to the ~/.machinaris/ folder and restart."
  else
    shibgreen start farmer-only
  fi
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ ! -f /root/.shibgreen/farmer_ca/private_ca.crt ]; then
      mkdir -p /root/.shibgreen/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8939/certificates/?type=shibgreen --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.shibgreen/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8939/certificates/?type=shibgreen.  Is the fork's fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.shibgreen/farmer_ca/private_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      shibgreen init -c /root/.shibgreen/farmer_ca 2>&1 > /root/.shibgreen/mainnet/log/init.log
      chmod 755 -R /root/.shibgreen/mainnet/config/ssl/ &> /dev/null
      shibgreen init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.shibgreen/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    echo "Configuring farmer peer at ${farmer_address}:${farmer_port}"
    shibgreen configure --set-farmer-peer ${farmer_address}:${farmer_port}
    shibgreen configure --enable-upnp false
    shibgreen start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
