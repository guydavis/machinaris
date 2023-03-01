# 
# Optionally builds and starts a timelord if environment variable of `mode` is `fullnode,timelord`
#

echo 'Attempting to build timelord binaries for this blockchain...'
apt update && apt install -y libgmp-dev libboost-python-dev libboost-system-dev
BUILD_VDF_CLIENT=Y BUILD_VDF_BENCH=Y /usr/bin/sh ./install-timelord.sh