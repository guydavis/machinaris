#
#  Configure and start plotting and farming services.
#

echo "Welcome to Machinaris!"

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

# Start only selected fork
for fork in ${blockchains//,/ }; do
  /usr/bin/bash /machinaris/scripts/forks/${fork}_launch.sh
done

# Launch Machinaris web server and other services
/machinaris/scripts/start_machinaris.sh

# Must build bladebit on target hardware on each container launch
/usr/bin/bash /machinaris/scripts/bladebit_build.sh > /tmp/bladebit_build.log 2>&1

# Cleanly stop Chia services on container stop/kill
trap "chia stop all -d; exit 0" SIGINT SIGTERM

while true; do sleep 30; done;
