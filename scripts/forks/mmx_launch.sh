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
	tee /root/.chia/mmx/config/local/Harvester.json >/dev/null <<EOF
{
	"plot_dirs": [ ${plot_dirs} ]
}
EOF
fi
rm -rf ./config
ln -s /root/.chia/mmx/config /mmx-node/config
escaped_plot_dirs=$(printf '%s\n' "$plot_dirs" | sed -e 's/[\/&]/\\&/g')
sed -i "s/\"plot_dirs\":.*$/\"plot_dirs\": [ $escaped_plot_dirs ]/g" ./config/local/Harvester.json

# Symlink the NETWORK file, use 'test3' for now
if [ ! -f /root/.chia/mmx/NETWORK ]; then
	echo 'test3' > /root/.chia/mmx/NETWORK
fi
rm -f ./NETWORK
ln -s /root/.chia/mmx/NETWORK /mmx-node/NETWORK

# Symlink the testnet3 folder
if [ ! -d /root/.chia/mmx/testnet3 ]; then
	mkdir /root/.chia/mmx/testnet3
fi
rm -rf ./testnet3
ln -s /root/.chia/mmx/testnet3 /mmx-node/testnet3

# Create a key if none found from previous runs
if [[ ${mode} == 'fullnode' ]]; then
	if [ ! -f /root/.chia/mmx/wallet.dat ]; then
		echo "Creating key at path: /root/.chia/mmx/wallet.dat"
		mmx wallet create
		mv wallet.dat /root/.chia/mmx/
	else
		echo "Adding key at path: /root/.chia/mmx/wallet.dat"
	fi
	if [ ! -L /mmx-node/wallet.dat ]; then
		ln -s /root/.chia/mmx/wallet.dat /mmx-node/wallet.dat
	fi
		# Setup log rotation
	tee /etc/logrotate.d/mmx-node >/dev/null <<EOF
	/root/.chia/mmx/logs/mmx_node.log {
	rotate 3
	daily
	}
EOF
	# Now start the MMX node
	./run_node.sh >/root/.chia/mmx/logs/mmx_node.log 2>&1 &
elif [[ ${mode} =~ ^farmer.* ]]; then
	# Setup log rotation
	tee /etc/logrotate.d/mmx-farmer >/dev/null <<EOF
	/root/.chia/mmx/logs/mmx_farmer.log {
	rotate 3
	daily
	}
EOF
	./run_farmer.sh -n ${node_address}:11330 >/root/.chia/mmx/logs/mmx_farmer.log 2>&1 &
elif [[ ${mode} =~ ^harvester.* ]]; then
	# Setup log rotation
	tee /etc/logrotate.d/mmx-harvester >/dev/null <<EOF
	/root/.chia/mmx/logs/mmx_harvester.log {
	rotate 3
	daily
	}
EOF
	./run_harvester.sh -n ${farmer_address}:11330 >/root/.chia/mmx/logs/mmx_harvester.log 2>&1 &
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
