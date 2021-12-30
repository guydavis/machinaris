#!/bin/env bash
#
# Initialize MMX node, depending on mode of system requested
#

cd /mmx-node

rm -rf ./logs
mkdir -p /root/.chia/mmx/logs
ln -s /root/.chia/mmx/logs logs

IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", \"%s\"" "${array[@]}")
plot_dirs=${joined:1}
echo $plot_dirs

if [ ! -d /root/.chia/mmx/config ]; then
	mv ./config /root/.chia/mmx/config
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
ln -s /root/.chia/mmx/config config
sed -i 's/"storage_path": ""/"storage_path": "\/root\/.chia\/mmx\/"/g' ./config/local/Node.json
escaped_plot_dirs=$(printf '%s\n' "$plot_dirs" | sed -e 's/[\/&]/\\&/g')
sed -i "s/\"plot_dirs\":.*$/\"plot_dirs\": [ $escaped_plot_dirs ]/g" ./config/local/Harvester.json

# Create a key if none found from previous runs
if [ ! -f /root/.chia/mmx/wallet.dat ]; then
	mmx wallet create -f /root/.chia/mmx/wallet.dat
	ln -s /root/.chia/mmx/wallet.dat /mmx-node/wallet.dat
fi

#echo "Current state of the $(pwd) folder:"
#ls -al .

./run_node.sh >/root/.chia/mmx/logs/mmx_node.log 2>&1 &
