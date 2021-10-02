#
#  Configure and start plotting and farming services.
#

# Print a wide line to ensure Unraid's Docker Logs view doesn't truncate the left-side of our logs
echo "Welcome! Machinaris is an easy-to-use WebUI for Chia plotting and farming. Includes Chia, Plotman, MadMax, Chiadog, Bladebit and Flax in a single Docker image."

# Always launch Chia - required blockchain
/usr/bin/bash /machinaris/scripts/chia_launch.sh

# Optionally launch forked blockchains for multi-farming
if [[ ${blockchains} =~ flax ]]; then
  /usr/bin/bash /machinaris/scripts/flax_launch.sh
fi

# Launch Machinaris web server and other services
/machinaris/scripts/start_machinaris.sh

while true; do sleep 30; done;
