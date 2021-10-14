#
#  Configure and start plotting and farming services.
#

echo "Welcome to Machinaris!"

# v0.6.0 upgrade check guard - only allow single blockchain per container
if [[ "${blockchains}" == "chia,flax" ]]; then
  echo "Only one blockchain allowed per container in Machinaris."
  echo "Please remove second value from 'blockchains' variable and restart."
  return 1
fi

# Start only selected fork
for fork in ${blockchains//,/ }; do
  /usr/bin/bash /machinaris/scripts/forks/${fork}_launch.sh
done

# Launch Machinaris web server and other services
/machinaris/scripts/start_machinaris.sh

# Check that bladebit works on local hardware
/usr/bin/bash /machinaris/scripts/bladebit_check.sh > /tmp/bladebit_check.log 2>&1

while true; do sleep 30; done;
