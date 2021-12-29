#!/bin/env bash
#
# Initialize MMX node, depending on mode of system requested
#

cd /mmx-node

rm -rf ./logs
mkdir -p /root/.chia/mmx/logs
ln -s /root/.chia/mmx/logs logs

rm -rf ./config
mkdir -p /root/.chia/mmx/config/local
ln -s /root/.chia/mmx/config config

echo "Current state of the $(pwd) folder:"
ls -al .

tee /root/.chia/mmx/config/local/Node.json >/dev/null <<EOF
{
	"opencl_device": 0,
	"storage_path": "/root/.chia/mmx/"
}
EOF

./run_node.sh >/root/.chia/mmx/logs/mmx_node.log 2>&1 &
