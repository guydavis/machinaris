#
#  Configure and start plotting and farming services.
#

echo "Welcome to Machinaris v$(cat /machinaris/VERSION)!"
echo "${blockchains} - ${mode} on $(uname -m)"

if [[ "$HOSTNAME" =~ " |'" ]]; then 
  echo "You have placed a space character in the hostname for this container."
  echo "Please use only alpha-numeric characters in the hostname within docker-compose.yml and restart."
  exit 1
fi

# v0.6.0 upgrade check guard - only allow single blockchain per container
if [[ "${blockchains}" == "chia,flax" ]]; then
  echo "Only one blockchain allowed per container in Machinaris."
  echo "Please remove second value from 'blockchains' variable and restart."
  exit 1
fi

# Ensure a worker_address containing an IP address is set on every launch, else exit
if [[ -z "${worker_address}" ]]; then
  echo "Please set the 'worker_address' environment variable to this system's IP address on your LAN."
  echo "https://github.com/guydavis/machinaris/wiki/Unraid#how-do-i-update-from-v05x-to-v060-with-fork-support"
  exit 1
fi

# v0.6.8 upgrade step - move location of plotnft.log
if [ -f /root/.chia/mainnet/log/plotnft.log ]; then
  mv /root/.chia/mainnet/log/plotnft.log /root/.chia/machinaris/logs/plotnft.log
fi

# v0.7.0 upgrade step - move location of cache json
if [[ ! -d /root/.chia/machinaris/cache ]] && [[ -f /root/.chia/machinaris/dbs/cold_wallet_cache.json ]] ; then
  mkdir -p /root/.chia/machinaris/cache
  mv /root/.chia/machinaris/dbs/*cache.json /root/.chia/machinaris/cache/
fi

# Refuse to run if Portainer launched containers out of order and created a directory for mnemonic.txt
if [[ "${mode}" == 'fullnode' ]] && [[ -d /root/.chia/mnemonic.txt ]]; then
  echo "Portainer (or similar) launched a fork container before the main Machinaris container on first run."
  echo "Attempting to delete the empty mnemonic.txt directory and restarting this fork container."
  rmdir /root/.chia/mnemonic.txt || true
  exit 1
fi

# Warn if non-standard worker_api_port is being used, likely default value they did not override properly
/usr/bin/bash /machinaris/scripts/worker_port_warning.sh 

# If on Windows, possibly mount SMB remote shares as defined in 'remote_shares' env var
/usr/bin/bash /machinaris/scripts/mount_remote_shares.sh > /tmp/mount_remote_shares.log

# Start the selected fork, then start Machinaris WebUI
if /usr/bin/bash /machinaris/scripts/forks/${blockchains}_launch.sh; then

  # Launch Machinaris web server and other services
  /machinaris/scripts/start_machinaris.sh

  # Cleanly stop Chia services on container stop/kill
  trap "chia stop all -d; exit 0" SIGINT SIGTERM

  # Conditionally install plotman on plotters and fullnodes, after the plotters setup
  /usr/bin/bash /machinaris/scripts/plotman_setup.sh > /tmp/plotman_setup.log 2>&1

  # Conditionally install chiadog on harvesters and fullnodes
  /usr/bin/bash /machinaris/scripts/chiadog_setup.sh ${CHIADOG_BRANCH} > /tmp/chiadog_setup.log 2>&1

  # During concurrent startup of multiple fork containers, stagger less important setups
  sleep $[ ( $RANDOM % 180 )  + 1 ]s

  # Conditionally install farmr on harvesters and fullnodes
  /usr/bin/bash /machinaris/scripts/farmr_setup.sh > /tmp/farmr_setup.log 2>&1

  # Conditionally install fd-cli on fullnodes, excluding Chia and Chives
  /usr/bin/bash /machinaris/scripts/fd-cli_setup.sh > /tmp/fd-cli_setup.log 2>&1

  # Conditionally build bladebit on plotters and fullnodes, sleep a bit first
  /usr/bin/bash /machinaris/scripts/bladebit_setup.sh ${BLADEBIT_BRANCH} > /tmp/bladebit_setup.log 2>&1

  # Conditionally madmax on plotters and fullnodes, sleep a bit first
  /usr/bin/bash /machinaris/scripts/madmax_setup.sh > /tmp/madmax_setup.log 2>&1

  # Conditionally install plotman on plotters and fullnodes, after the plotters setup
  /usr/bin/bash /machinaris/scripts/plotman_autoplot.sh > /tmp/plotman_autoplot.log 2>&1

  # Conditionally install forktools on fullnodes
  /usr/bin/bash /machinaris/scripts/forktools_setup.sh > /tmp/forktools_setup.log 2>&1

fi

while true; do sleep 30; done;
