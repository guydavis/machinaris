#!/bin/env bash
#
# Initialize Chia service, depending on mode of system requested
#

if [[ "${mode}" == 'fullnode' ]]; then
  touch /root/.chia/mnemonic.txt
  chmod 600 /root/.chia/mnemonic.txt
fi

# Ensure Chia keyring is held on a persistent volume
mkdir -p /root/.chia/.chia_keys
rm -f /root/.chia_keys
ln -s /root/.chia/.chia_keys /root/.chia_keys

#cd /chia-blockchain
#. ./activate

if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f /root/.chia/mainnet/db/blockchain_v1_mainnet.sqlite ]] \
  && [[ ! -f /root/.chia/mainnet/db/blockchain_v2_mainnet.sqlite ]]; then
  # Create machinaris dbs and launch web only while blockchain database downloads
  . /machinaris/scripts/setup_databases.sh
  mkdir -p /root/.chia/machinaris/config
  mkdir -p /root/.chia/machinaris/logs
  cd /machinaris
  /chia-blockchain/venv/bin/gunicorn \
     --bind 0.0.0.0:8926 --timeout 90 \
      --log-level=info \
      --workers=2 \
      --log-config web/log.conf \
      web:app &
  echo 'Starting web server...  Browse to port 8926.'
  echo "Downloading Chia blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as this takes hours now, but saves days of syncing time later."
  mkdir -p /root/.chia/mainnet/db/chia && cd /root/.chia/mainnet/db/chia
  # Latest Blockchain DB via torrent download
  torrent=$(curl -s https://www.chia.net/downloads/ | grep -Po "https://torrents.chia.net/databases/mainnet/mainnet.\d{4}-\d{2}-\d{2}.tar.gz.torrent")
  echo "Please be patient! Downloading blockchain database indirectly (via libtorrent) from: "
  echo "    ${torrent}"
  curl -skLJ -O ${torrent}
  /usr/bin/python /machinaris/scripts/chiadb_download.py $PWD/*.torrent >> /tmp/chiadb_download.log 2>&1
  echo "Now decompressing the blockchain database..."
  cd /root/.chia/mainnet/db/chia && tar -xf *.gz
  mv blockchain_v2_mainnet.sqlite height-to-hash ..
  cd /root/.chia/mainnet/db
  rm -rf /root/.chia/mainnet/db/chia
fi

mkdir -p /root/.chia/mainnet/log
chia init >> /root/.chia/mainnet/log/init.log 2>&1

echo 'Configuring Chia...'
if [ ! -f /root/.chia/mainnet/config/config.yaml ]; then
  sleep 60  # Give Chia long enough to initialize and create a config file...
fi
if [ -f /root/.chia/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' /root/.chia/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.chia/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' /root/.chia/mainnet/config/config.yaml
fi

# Loop over provided list of key paths
label_num=0
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -s ${k} ]; then
    echo "Adding key #${label_num} at path: ${k}"
    chia keys add -l "key_${label_num}" -f ${k} > /dev/null
    ((label_num=label_num+1))
  elif [[ ${mode} =~ ^fullnode.* ]]; then
    echo "Skipping 'chia keys add' as no file found at: ${k}"
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
    chia plots add -d ${p}
done

chmod 755 -R /root/.chia/mainnet/config/ssl/ &> /dev/null
chia init --fix-ssl-permissions >/dev/null 2>&1  

/usr/bin/bash /machinaris/scripts/gpu_drivers_setup.sh

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} =~ ^fullnode.* ]]; then
  if [ -f /root/.chia/machinaris/config/wallet_settings.json ]; then
    chia start farmer-no-wallet
  else
    chia start farmer
  fi
  if [[ ${chia_exporter} == "true" ]]; then
    echo "Starting Chia Exporter service for Prometheus reporting..."
    sleep 20 && /usr/local/bin/chia-exporter serve 2>&1 > /root/.chia/mainnet/log/chia-exporter.log &
  fi
  if [[ ${chia_data} == "true" ]]; then
    echo "Starting Chia Data Layer services..."
    sleep 20 && chia start data 2>&1 > /root/.chia/mainnet/log/chia-data.log &
    sleep 20 && chia start data_layer_http 2>&1 >> /root/.chia/mainnet/log/chia-data.log &
  fi
  if [[ ${mode} =~ .*timelord$ ]]; then
    if [ ! -f vdf_bench ]; then
        echo "Building timelord binaries..."
        apt-get update > /tmp/timelord_build.sh 2>&1 
        apt-get install -y libgmp-dev libboost-python-dev libboost-system-dev >> /tmp/timelord_build.sh 2>&1 
        BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh >> /tmp/timelord_build.sh 2>&1 
    fi
    chia start timelord-only
  fi
elif [[ ${mode} =~ ^farmer.* ]]; then
  chia start farmer-only
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit 1
  else
    if [ ! -f /root/.chia/farmer_ca/chia_ca.crt ]; then
      mkdir -p /root/.chia/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8927/certificates/?type=chia --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d /root/.chia/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8927/certificates/?type=chia.  Is the Machinaris fullnode container running?"
      fi
      rm -f /tmp/certs.zip 
    fi
    if [[ -f /root/.chia/farmer_ca/chia_ca.crt ]] && [[ ! ${keys} == "persistent" ]]; then
      chia init -c /root/.chia/farmer_ca 2>&1 > /root/.chia/mainnet/log/init.log
      chmod 755 -R /root/.chia/mainnet/config/ssl/ &> /dev/null
      chia init --fix-ssl-permissions >/dev/null 2>&1   
    else
      echo "Did not find your farmer's certificates within /root/.chia/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    chia configure --set-farmer-peer ${farmer_address}:${farmer_port}  2>&1 >> /root/.chia/mainnet/log/init.log
    chia configure --enable-upnp false  2>&1 >> /root/.chia/mainnet/log/init.log
    chia start harvester -r
    if [[ ${chia_exporter} == "true" ]]; then
      echo "Starting Chia Exporter service for Prometheus reporting..."
      sleep 20 && /usr/local/bin/chia-exporter serve 2>&1 > /root/.chia/mainnet/log/chia-exporter.log &
    fi
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
