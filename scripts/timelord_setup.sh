# 
# Optionally builds and starts a timelord if environment variable of `mode` is `fullnode,timelord`
#

# runs from the /FORK-blockchain folder via the /machinaris/scripts/forks/FORK_launch.sh script
if [ ! -f vdf_bench ]; then
    apt update 2>&1 > /tmp/timelord_build.sh
    apt install -y libgmp-dev libboost-python-dev libboost-system-dev 2>&1 >> /tmp/timelord_build.sh
    BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh 2>&1 >> /tmp/timelord_build.sh
fi
