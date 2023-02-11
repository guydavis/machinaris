#!/bin/env bash
#
# Initialize Gigahorse farmer or harvester (also optionally plotter)
#

cd /chia-gigahorse-farmer

. ./activate.sh

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
  # Fix port conflicts with other blockchains like Chia.
  #sed -i 's/8444/28445/g' /root/.sit/mainnet/config/config.yaml
  sed -i 's/8445/28446/g' /root/.sit/mainnet/config/config.yaml
  #sed -i 's/8555/28556/g' /root/.sit/mainnet/config/config.yaml
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

# Start services based on mode selected. Gigahorse should NOT be a fullnode within Machinaris.
if [[ ${mode} == 'fullnode' ]]; then
  echo "Please run as a farmer instead of fullnode."
  exit -1
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
