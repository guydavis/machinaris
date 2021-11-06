#!/bin/env bash
#
# If user has optionally enabled farmr by saving a config file, 
# then launch it on container start
#

# Only the /root/.chia folder is volume-mounted so store farmr within
mkdir -p /root/.chia/farmr
rm -f /root/.farmr
ln -s /root/.chia/farmr /root/.farmr 

# TODO When to start farmr in background via nohup
