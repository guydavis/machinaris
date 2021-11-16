#
#  Configure and start plotting and farming services.
#

echo "Welcome to Machinaris! - v$(cat /machinaris/VERSION) - ${mode}"

# v0.6.0 upgrade check guard - only allow single blockchain per container
if [[ "${blockchains}" == "chia,flax" ]]; then
  echo "Only one blockchain allowed per container in Machinaris."
  echo "Please remove second value from 'blockchains' variable and restart."
  exit 1
fi

if [[ -z "${worker_address}" ]]; then
  echo "Please set the 'worker_address' environment variable to this system's IP address on your LAN."
  echo "https://github.com/guydavis/machinaris/wiki/Unraid#how-do-i-update-from-v05x-to-v060-with-fork-support"
  exit 1
fi

# If on Windows, possibly mount SMB remote shares as defined in 'remote_shares' env var
/usr/bin/bash /machinaris/scripts/mount_remote_shares.sh > /tmp/mount_remote_shares.log

# Conditionally install megacmd on fullnodes
/usr/bin/bash /machinaris/scripts/megacmd_setup.sh > /tmp/megacmd_setup.log 2>&1

# Start the selected fork, then start Machinaris WebUI
if /usr/bin/bash /machinaris/scripts/forks/${blockchains}_launch.sh; then

  # Launch Machinaris web server and other services
  /machinaris/scripts/start_machinaris.sh

  # Cleanly stop Chia services on container stop/kill
  trap "chia stop all -d; exit 0" SIGINT SIGTERM

  # During concurrent startup of multiple fork containers, stagger setups
  sleep $[ ( $RANDOM % 90 )  + 1 ]s

  # Conditionally install plotman on plotters and fullnodes, after the plotters setup
  /usr/bin/bash /machinaris/scripts/plotman_setup.sh > /tmp/plotman_setup.log 2>&1

  # Conditionally install chiadog on harvesters and fullnodes
  /usr/bin/bash /machinaris/scripts/chiadog_setup.sh > /tmp/chiadog_setup.log 2>&1

  # Conditionally install farmr on harvesters and fullnodes
  /usr/bin/bash /machinaris/scripts/farmr_setup.sh > /tmp/farmr_setup.log 2>&1

  # Conditionally install fd-cli on fullnodes, excluding Chia and Chives
  /usr/bin/bash /machinaris/scripts/fd-cli_setup.sh > /tmp/fd-cli_setup.log 2>&1

  # Conditionally build bladebit on plotters and fullnodes, sleep a bit first
  /usr/bin/bash /machinaris/scripts/bladebit_setup.sh > /tmp/bladebit_setup.log 2>&1

  # Conditionally madmax on plotters and fullnodes, sleep a bit first
  /usr/bin/bash /machinaris/scripts/madmax_setup.sh > /tmp/madmax_setup.log 2>&1

  # Conditionally install plotman on plotters and fullnodes, after the plotters setup
  /usr/bin/bash /machinaris/scripts/plotman_autoplot.sh > /tmp/plotman_autoplot.log 2>&1

fi

while true; do sleep 30; done;
