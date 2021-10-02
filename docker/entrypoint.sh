#
#  Configure and start plotting and farming services.
#

echo "Welcome to Machinaris!"

# Start selected forks
for fork in ${blockchains//,/ }; do
  /usr/bin/bash /machinaris/scripts/forks/${fork}_launch.sh
done

# Launch Machinaris web server and other services
/machinaris/scripts/start_machinaris.sh

while true; do sleep 30; done;
