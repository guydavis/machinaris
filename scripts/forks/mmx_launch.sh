#!/bin/env bash
#
# Initialize MMX node, depending on mode of system requested
#

cd /mmx-node

rm -rf ./logs
mkdir -p /root/.chia/mmx/logs
ln -s /root/.chia/mmx/logs logs

rm -rf ./logs
mkdir -p /root/.chia/mmx/config/local
ln -s /root/.chia/mmx/config config

./run_node.sh >/root/.chia/mmx/logs/mmx_node.log 2>&1 &
