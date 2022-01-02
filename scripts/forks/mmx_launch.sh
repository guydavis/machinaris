#!/bin/env bash
#
# Initialize MMX node, depending on mode of system requested
#

cd /mmx-node

rm -rf ./logs
mkdir -p /root/.chia/mmx/logs
ln -s /root/.chia/mmx/logs /mmx-node/logs
ln -s /root/.chia/mmx /root/.mmx 

IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", \"%s\"" "${array[@]}")
plot_dirs=${joined:1}
echo "Adding plot directories at: ${plot_dirs}"

# Setup configuration for MMX inside a Docker container
if [ ! -d /root/.chia/mmx/config ]; then
	mv ./config /root/.chia/mmx/
	mkdir -p /root/.chia/mmx/config/local
	tee /root/.chia/mmx/config/local/Node.json >/dev/null <<EOF
{
	"opencl_device": 0,
	"storage_path": "/root/.chia/mmx/"
}
EOF
	tee /root/.chia/mmx/config/local/Harvester.json >/dev/null <<EOF
{
	"plot_dirs": [ ${plot_dirs} ]
}
EOF
fi
rm -rf ./config
ln -s /root/.chia/mmx/config /mmx-node/config
sed -i 's/"storage_path": ""/"storage_path": "\/root\/.chia\/mmx\/"/g' ./config/local/Node.json
escaped_plot_dirs=$(printf '%s\n' "$plot_dirs" | sed -e 's/[\/&]/\\&/g')
sed -i "s/\"plot_dirs\":.*$/\"plot_dirs\": [ $escaped_plot_dirs ]/g" ./config/local/Harvester.json

# Create a key if none found from previous runs
if [ ! -f /root/.chia/mmx/wallet.dat ]; then
	echo "Creating key at path: /root/.chia/mmx/wallet.dat"
	mmx wallet create -f /root/.chia/mmx/wallet.dat
	ln -s /root/.chia/mmx/wallet.dat /mmx-node/wallet.dat
else
	echo "Adding key at path: /root/.chia/mmx/wallet.dat"
fi

# Symlink the known_peers database file
if [ ! -f /root/.chia/mmx/known_peers.dat ]; then
	if [ -f ./known_peers.dat ]; then
		mv ./known_peers.dat /root/.chia/mmx/known_peers.dat
	else
		touch /root/.chia/mmx/known_peers.dat
	fi 
fi
rm -f ./known_peers.dat
ln -s /root/.chia/mmx/known_peers.dat /mmx-node/known_peers.dat

# Symlink the NETWORK file, use 'test2' for now
if [ ! -f /root/.chia/mmx/NETWORK ]; then
	echo 'test2' > /root/.chia/mmx/NETWORK
fi
rm -f ./NETWORK
ln -s /root/.chia/mmx/NETWORK /mmx-node/NETWORK

# Now start the MMX node
./run_node.sh >/root/.chia/mmx/logs/mmx_node.log 2>&1 &
