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

# Support for GPUs used when plotting/farming
if [[ ${OPENCL_GPU} == 'nvidia' ]]; then   
    mkdir -p /etc/OpenCL/vendors
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd
    echo "Enabling Nvidia GPU support inside this container."
elif [[ ${OPENCL_GPU} == 'amd' ]]; then
	pushd /tmp > /dev/null
  echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
	apt-get update 2>&1 > /tmp/amdgpu_setup.log
	amdgpu-install -y --usecase=opencl --opencl=rocr --no-dkms --no-32 --accept-eula 2>&1 >> /tmp/amdgpu_setup.log
	popd > /dev/null
  echo "Enabling AMD GPU support inside this container."
elif [[ ${OPENCL_GPU} == 'intel' ]]; then
	apt-get update 2>&1 > /tmp/intelgpu_setup.log
	apt-get install -y intel-opencl-icd 2>&1 >> /tmp/intelgpu_setup.log
  echo "Enabling Intel GPU support inside this container."
else
	echo "No OPENCL_GPU provided.  MMX blockchain will use use CPU instead."
fi

echo 'testnet9' > /root/.chia/mmx/NETWORK

# Symlink the testnet9 folder
if [ ! -d /root/.chia/mmx/testnet9 ]; then
	mkdir /root/.chia/mmx/testnet9
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
