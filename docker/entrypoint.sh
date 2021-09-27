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

# Build bladebit plotter on first run of container
/usr/bin/bash /machinaris/scripts/bladebit_make.sh > /tmp/bladebit_make.log 2>&1 

while true; do sleep 30; done;
