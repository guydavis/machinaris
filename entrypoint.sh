#
# Original version: https://github.com/Chia-Network/chia-docker/blob/main/entrypoint.sh
#   - added first launch should automatically generate keys if not present
#   - Plotter-only mode for systems to just run Plotman
#   - Launch the Machinaris web server in the background
# 

cd /chia-blockchain

. ./activate

chia init

if [[ ${keys} == "generate" ]]; then
  echo "to use your own keys pass them as a text file -v /path/to/keyfile:/path/in/container and -e keys=\"/path/in/container\""
  chia keys generate
elif [[ ! -f ${keys} ]]; then
  echo "no such keys file yet, so probably first launch, generating keys and storing mnemonic now..."
  chia keys generate
  chia keys show --show-mnemonic-seed | tail -n 1 > /root/.chia/mnemonic.txt
else
  chia keys add -f ${keys}
fi

if [[ ! "$(ls -A /plots)" ]]; then
  echo "Plots directory appears to be empty and you have not specified another, try mounting a plot directory with the docker -v command "
fi

for p in ${plots_dir//:/ }; do
    chia plots add -d ${p}
done

sed -i 's/localhost/127.0.0.1/g' ~/.chia/mainnet/config/config.yaml

if [[ ${farmer} == 'true' ]]; then
  chia start farmer-only
elif [[ ${harvester} == 'true' ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit
  else
    chia configure --set-farmer-peer ${farmer_address}:${farmer_port}
    chia start harvester
  fi
elif [[ ${plotter} == 'true' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
else
  chia start farmer
fi

if [[ ${testnet} == "true" ]]; then
  if [[ -z $full_node_port || $full_node_port == "null" ]]; then
    chia configure --set-fullnode-port 58444
  else
    chia configure --set-fullnode-port ${var.full_node_port}
  fi
fi

# Launch Machinaris web server
/machinaris/start.sh

while true; do sleep 30; done;