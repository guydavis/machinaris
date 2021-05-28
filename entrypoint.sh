#
#  Configure and launch services for farming, harvesting, and plotting 
#  Original: https://github.com/Chia-Network/chia-docker/blob/main/entrypoint.sh
#   - Improved key generation via webui when no keys found
#   - Add plotter-only mode for systems to just run Plotman
#   - Launch the Machinaris web server in the background
#

cd /chia-blockchain

. ./activate

mkdir -p /root/.chia/mainnet/log
chia init 2>&1 > /root/.chia/mainnet/log/init.log

# Loop over provided list of key paths
for k in ${keys//:/ }; do
  echo "Adding key at path: {$k}"
  chia keys add -f ${k} > /dev/null
done

# Loop over provided list of completed plot directories
for p in ${plots_dir//:/ }; do
    chia plots add -d ${p}
done

sed -i 's/localhost/127.0.0.1/g' ~/.chia/mainnet/config/config.yaml

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'farmer' ]]; then
  chia start farmer-only
elif [[ ${mode} == 'harvester' ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    if [ -d /root/.chia/farmer_ca ]; then
      chia init -c /root/.chia/farmer_ca 2>&1 > /root/.chia/mainnet/log/init.log
    else
      echo "Did not find your farmer's ca folder at /root/.chia/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Generic#harvester-only"
    fi
    chia configure --set-farmer-peer ${farmer_address}:${farmer_port}
    chia configure --enable-upnp false
    chia start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
else  
  chia start farmer
fi

# Optionally use testnet instead of mainnet
if [[ ${testnet} == "true" ]]; then
  if [[ -z $full_node_port || $full_node_port == "null" ]]; then
    chia configure --set-fullnode-port 58444
  fi
fi

# Once per launch, try to get past wallet prompt
echo 'S' | chia wallet show > /dev/null || true

# Launch Machinaris web server and other services
/machinaris/scripts/start-machinaris.sh

while true; do sleep 30; done;
