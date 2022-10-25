#!/bin/env bash
#
# Initialize MMX node, depending on mode of system requested
#

cd /mmx-node

mkdir -p /root/.chia/mmx/logs
if [ ! -L /root/.mmx ]; then
	ln -s /root/.chia/mmx /root/.mmx
fi

echo "Launching MMX with storage at: ${MMX_HOME}"

IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", \"%s\"" "${array[@]}")
plot_dirs=${joined:1}
echo "Adding plot directories at: ${plot_dirs}"

# Setup configuration for MMX inside a Docker container
if [ ! -d /root/.chia/mmx/config ]; then
	mkdir -p /root/.chia/mmx/config/local
	tee /root/.chia/mmx/config/local/Harvester.json >/dev/null <<EOF
{
	"plot_dirs": [ ${plot_dirs} ]
}
EOF
	# For a fresh install of Machinaris-MMX, disable timelord by default to save CPU usage
	echo false > /root/.chia/mmx/config/local/timelord
fi
escaped_plot_dirs=$(printf '%s\n' "$plot_dirs" | sed -e 's/[\/&]/\\&/g')
sed -i "s/\"plot_dirs\":.*$/\"plot_dirs\": [ $escaped_plot_dirs ]/g" /root/.chia/mmx/config/local/Harvester.json

if [[ ${OPENCL_GPU} == 'nvidia' ]]; then    
    mkdir -p /etc/OpenCL/vendors
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd
elif [[ ${OPENCL_GPU} == 'amd' ]]; then
	cd /tmp
	apt update
	amdgpu-install -y --usecase=opencl --opencl=rocr --no-dkms --no-32 --accept-eula
	# If AMD GPU is older than vega 10,use under command, but can't promise work normally.
	# Because, with --opencl=legacy, dkms will must be installed, it may pollute your kernel
	# amdgpu-install -y --usecase=opencl --opencl=rocr,legacy --no-32 --accept-eula
elif [[ ${OPENCL_GPU} == 'intel' ]]; then
	apt update
	apt install -y intel-opencl-icd
else
	echo "No OPENCL_GPU provided.  MMX blockchain will use use CPU instead."
fi

echo 'testnet8' > /root/.chia/mmx/NETWORK

# Symlink the testnet8 folder
if [ ! -d /root/.chia/mmx/testnet8 ]; then
	mkdir /root/.chia/mmx/testnet8
fi

# Create a key if none found from previous runs
if [[ ${mode} == 'fullnode' ]]; then
	if [ ! -f /root/.chia/mmx/wallet.dat ]; then
		echo "Creating key at path: /root/.chia/mmx/wallet.dat"
		mmx wallet create
	else
		echo "Adding key at path: /root/.chia/mmx/wallet.dat"
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
