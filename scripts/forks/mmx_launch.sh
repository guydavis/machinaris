#!/bin/env bash
#
# Initialize MMX node, depending on mode of system requested
#

cd /mmx-node
mkdir -p /root/.chia/mmx/logs
ln -s /root/.chia/mmx/logs logs
mkdir -p /root/.chia/mmx/config/local
ln -s /root/.chia/mmx/config config

./run_node.sh
