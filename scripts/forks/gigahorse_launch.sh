#!/bin/env bash
#
# Initialize Gigahorse farmer or harvester (also optionally plotter)
#

cd /chia-gigahorse-farmer

. ./activate.sh

mkdir -p /root/.chia/mainnet/log
chia init >> /root/.chia/mainnet/log/init.log 2>&1

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
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  mkdir -p /root/.chia/mainnet/db/chia && cd /root/.chia/mainnet/db/chia
  # Latest Blockchain DB download from direct from https://sweetchia.com/
  db_url=$(curl -s https://sweetchia.com | grep -Po "https:.*/blockchain_v2_mainnet-\d{4}-\d{2}-\d{2}-\d{4}.7z" | shuf -n 1)
  echo "Please be patient! Downloading blockchain database from: "
  echo "    ${db_url}"
  curl -skLJ -O ${db_url}
  p7zip --decompress --force blockchain_v2_mainnet*.7z
  cd /root/.chia/mainnet/db
  mv /root/.chia/mainnet/db/chia/blockchain_v2_mainnet.sqlite .
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
  # Fix port conflicts with other fullnodes like Chia.
  #sed -i 's/8444/28445/g' /root/.chia/mainnet/config/config.yaml
  #sed -i 's/8445/28446/g' /root/.chia/mainnet/config/config.yaml
  #sed -i 's/8555/28556/g' /root/.chia/mainnet/config/config.yaml
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
  elif [[ ${mode} == 'fullnode' ]]; then
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
chia init --fix-ssl-permissions > /dev/null 

# Support for GPUs used when plotting/farming
if [[ ${OPENCL_GPU} == 'nvidia' ]]; then   
    mkdir -p /etc/OpenCL/vendors
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd
    echo "Enabling Nvidia GPU support inside this container."
elif [[ ${OPENCL_GPU} == 'amd' ]]; then
	pushd /tmp > /dev/null
  echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
	apt-get update 2>&1 > /tmp/amdgpu_setup.log
	amdgpu-install -y --usecase=opencl --opencl=rocr --no-dkms --no-32 --accept-eula 2>&1 >> /tmp/amdgpu_setup.log
	popd > /dev/null
  echo "Enabling AMD GPU support inside this container."
elif [[ ${OPENCL_GPU} == 'intel' ]]; then
  echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
	apt-get update 2>&1 > /tmp/intelgpu_setup.log
	apt-get install -y intel-opencl-icd 2>&1 >> /tmp/intelgpu_setup.log
  echo "Enabling Intel GPU support inside this container."
fi

# Start services based on mode selected. Always skip a duplicate Chia wallet launch
if [[ ${mode} == 'fullnode' ]]; then
  chia start farmer-no-wallet
elif [[ ${mode} =~ ^farmer.* ]]; then
  # TODO: Change farmer's fullnode_peer to ${controller_host} in config.yaml
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
      chia init --fix-ssl-permissions > /dev/null 
    else
      echo "Did not find your farmer's certificates within /root/.chia/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    chia configure --set-farmer-peer ${farmer_address}:${farmer_port}
    chia configure --enable-upnp false
    chia start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
