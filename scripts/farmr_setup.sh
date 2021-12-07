#!/bin/env bash
#
# Installs farmr - https://github.com/gilnobrega/farmr
#
if [[ ${blockchains} == 'shibgreen' ]]; then
	echo 'Sorry, ${blockchains} not supported by Farmr. Nothing started...'
elif [[ ${mode} == 'fullnode' ]] || [[ ${mode} =~ "harvester" ]]; then
    if [[ ! -f /usr/bin/farmr ]]; then
		arch_name="$(uname -m)"
		echo "Installing farmr on ${arch_name}..."
		cd /tmp
		if [[ "${arch_name}" = "x86_64" ]]; then
			curl -LJO https://github.com/joaquimguimaraes/farmr/releases/latest/download/farmr-ubuntu-x86_64.deb
			apt install ./farmr-ubuntu-x86_64.deb
			rm -f ./farmr-ubuntu-x86_64.deb
		elif [[ "${arch_name}" = "aarch64" ]]; then
			curl -LJO https://github.com/joaquimguimaraes/farmr/releases/latest/download/farmr-ubuntu-aarch64.deb
			apt install ./farmr-ubuntu-aarch64.deb
			rm -f ./farmr-ubuntu-aarch64.deb
		else
			echo "Installing farmr skipped -> unsupported architecture: ${arch_name}"
		fi
	fi
		
	# Only the /root/.chia folder is volume-mounted so store farmr within
	mkdir -p /root/.chia/farmr
	rm -f /root/.farmr
	ln -s /root/.chia/farmr /root/.farmr 

	cd /root/.farmr

	if [[ ! -d ./blockchain ]]; then # Never run before, will create default configs
		nohup farmr 2>&1 >/dev/null &
		sleep 30
		kill $(pidof farmr)
	fi

	if [[ ${blockchains} != "chia" ]] && [[ -f blockchain/xch.json ]]; then
		mv -f blockchain/xch.json blockchain/xch.json.template
	fi

	if [[ ${blockchains} == 'btcgreen' ]]; then
		cp -n blockchain/xbtc.json.template blockchain/xbtc.json
		echo "/btcgreen-blockchain/venv/bin/btcgreen" > override-xbtc-binary.txt
	elif [[ ${blockchains} == 'cactus' ]]; then
		cp -n blockchain/cac.json.template blockchain/cac.json
		echo "/cactus-blockchain/venv/bin/cactus" > override-cac-binary.txt
	elif [[ ${blockchains} == 'chia' ]]; then
		echo "/chia-blockchain/venv/bin/chia" > override-xch-binary.txt
	elif [[ ${blockchains} == 'chives' ]]; then
		cp -n blockchain/xcc.json.template blockchain/xcc.json
		echo "/chives-blockchain/venv/bin/chives" > override-xcc-binary.txt
	elif [[ ${blockchains} == 'cryptodoge' ]]; then
		cp -n blockchain/xcd.json.template blockchain/xcd.json
		echo "/cryptodoge-blockchain/venv/bin/cryptodoge" > override-xcd-binary.txt
	elif [[ ${blockchains} == 'flax' ]]; then
		cp -n blockchain/xfx.json.template blockchain/xfx.json
		echo "/flax-blockchain/venv/bin/flax" > override-xfx-binary.txt
	elif [[ ${blockchains} == 'flora' ]]; then
		cp -n blockchain/xfl.json.template blockchain/xfl.json
		echo "/flora-blockchain/venv/bin/flora" > override-xfl-binary.txt
	elif [[ ${blockchains} == 'hddcoin' ]]; then
		cp -n blockchain/hdd.json.template blockchain/hdd.json
		echo "/hddcoin-blockchain/venv/bin/hddcoin" > override-hdd-binary.txt
	elif [[ ${blockchains} == 'maize' ]]; then
		cp -n blockchain/xmz.json.template blockchain/xmz.json
		echo "/maize-blockchain/venv/bin/maize" > override-xmz-binary.txt
	elif [[ ${blockchains} == 'nchain' ]]; then
		cp -n blockchain/nch.json.template blockchain/nch.json
		echo "/chia-blockchain/venv/bin/chia" > override-nch-binary.txt
	elif [[ ${blockchains} == 'staicoin' ]]; then
		cp -n blockchain/stai.json.template blockchain/stai.json
		echo "/staicoin-blockchain/venv/bin/staicoin" > override-stai-binary.txt
	elif [[ ${blockchains} == 'stor' ]]; then
		cp -n blockchain/stor.json.template blockchain/stor.json
		echo "/stor-blockchain/venv/bin/stor" > override-stor-binary.txt
	fi

	tee /etc/logrotate.d/farmr > /dev/null <<EOF
/root/.chia/farmr/log*txt {
  rotate 3
  hourly
}
EOF

	if [[ ! -z "${farmr_skip_launch}" ]]; then
		rm -f nohup.out # Remove stale stdout logging
		# Launch in harvester or farmer mode
		if [[ ${mode} =~ ^harvester.* ]]; then
			(sleep 180 && nohup /usr/bin/farmr harvester headless 2>&1 ) &
		elif [[ ${mode} == 'farmer' ]] || [[ ${mode} == 'fullnode' ]]; then
			(sleep 180 && nohup /usr/bin/farmr farmer headless 2>&1 ) &
		fi
	fi
fi
