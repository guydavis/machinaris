#!/bin/env bash
#
# Installs farmr for optionally monitoring
#

arch_name="$(uname -m)"
echo "Installing farmr on ${arch_name}..."
cd /tmp
if [[ "${arch_name}" = "x86_64" ]]; then
    curl -LJO https://github.com/joaquimguimaraes/farmr/releases/latest/download/farmr-ubuntu-x86_64.deb
	apt install ./farmr-ubuntu-x86_64.deb
elif [[ "${arch_name}" = "aarch_64" ]]; then
	curl -LJO https://github.com/joaquimguimaraes/farmr/releases/latest/download/farmr-ubuntu-aarch64.deb
	apt install ./farmr-ubuntu-aarch64.deb
else
    echo "Installing farmr skipped -> unsupported architecture: ${arch_name}"
fi