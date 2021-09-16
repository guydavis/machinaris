#!/bin/env bash
#
# Creates default settings for the Machinaris API server
#

if [ ! -f "${API_SETTINGS_FILE}" ]; then
    mkdir -p /root/.chia/machinaris/config
    arch_name="$(uname -m)"
    echo "Configuring API server for arch_name=${arch_name}"
    if [ "${arch_name}" = "aarch64" ]; then
        if [ "${mode}" == "fullnode" ]; then
            echo "STATUS_EVERY_X_MINUTES = 4" > ${API_SETTINGS_FILE}
        fi
    fi
    cat ${API_SETTINGS_FILE}
fi
