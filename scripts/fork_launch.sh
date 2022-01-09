#!/bin/env bash
#
# Initialize Chia/-fork service, depending on mode of system requested
#

FORK_CMD=${FORK_CMD:-${blockchains}}
FORK_INSTALL_DIR=${FORK_INSTALL_DIR:-"/${blockchains}-blockchain"}
FORK_CONFIG_DIR=${FORK_CONFIG_DIR:-/root/.chia/${blockchains}}
FORK_CONFIG_LINK=${FORK_CONFIG_LINK:-$(basename $FORK_CONFIG_DIR | sed 's/^\.//')}

if [[ "${mode}" == 'fullnode' ]]; then
  touch /root/.chia/mnemonic.txt
  chmod 600 /root/.chia/mnemonic.txt
fi

# Ensure Chia keyring is held on a persistent volume
if [ ! -L "/root/.${FORK_CONFIG_LINK}_keys" ] ; then
  mkdir -p /root/.chia/.${FORK_CONFIG_LINK}_keys
  rm -rf --one-file-system /root/.${FORK_CONFIG_LINK}_keys
  ln -s /root/.chia/.${FORK_CONFIG_LINK}_keys /root/.${FORK_CONFIG_LINK}_keys
fi

# Ensure blockchain is on persistent volume
if [ ! -L "/root/.${FORK_CONFIG_LINK}" ] ; then
  mkdir -p /root/.chia/${FORK_CONFIG_LINK}
  rm -rf --one-file-system "/root/.${FORK_CONFIG_LINK}"
  ln -s ${FORK_CONFIG_DIR} /root/.${FORK_CONFIG_LINK}
fi

cd ${FORK_INSTALL_DIR}
. ./activate

mkdir -p ${FORK_CONFIG_DIR}/mainnet/log
${FORK_CMD} init >> ${FORK_CONFIG_DIR}/mainnet/log/init.log 2>&1

# Download Blockchain
if [[ "${blockchain_db_download}" == 'true' ]] \
  && [[ "${mode}" == 'fullnode' ]] \
  && [[ ! -f ${FORK_CONFIG_DIR}/mainnet/db/blockchain_v1_mainnet.sqlite ]]; then
  echo "Downloading ${blockchains} blockchain DB (many GBs in size) on first launch..."
  echo "Please be patient as takes minutes now, but saves days of syncing time later."
  # Create machinaris dbs and launch web only while blockchain database downloads
  . /machinaris/scripts/setup_databases.sh
  mkdir -p /root/.chia/machinaris/config /root/.chia/machinaris/logs

  echo 'Starting web server...  Browse to port 8926.'
  ${FORK_INSTALL_DIR}/venv/bin/gunicorn \
     --bind 0.0.0.0:8926 --timeout 90 \
      --log-level=info \
      --workers=2 \
      --log-config web/log.conf \
      web:app &
  mkdir -p ${FORK_CONFIG_DIR}/mainnet/db/chia && cd ${FORK_CONFIG_DIR}/mainnet/db/chia

  if [ "$blockchains" == "chia" ] ; then
    # Latest Blockchain DB download from direct from https://www.chia-database.com/
    file_time=$(curl -s https://chia-database.com | grep -Po "blockchain_v1_mainnet-\K(\d|-)+")
    curl -kLJ -o - https://nginx.chia-database.com/blockchain_v1_mainnet-${file_time}.zip | zcat >> /root/.chia/mainnet/db/blockchain_v1_mainnet.sqlite
  else
    echo "Sorry, ${blockchains} is currently not supported for blockchain DB download."
    echo "It is recommended to add some peer node connections on the Connections page of Machinaris from: https://alltheblocks.net/${blockchains}"
  fi
fi


echo "Configuring ${blockchains}..."
if [ -f ${FORK_CONFIG_DIR}/mainnet/config/config.yaml ]; then
  sed -i 's/log_stdout: true/log_stdout: false/g' ${FORK_CONFIG_DIR}/mainnet/config/config.yaml
  sed -i 's/log_level: WARNING/log_level: INFO/g' ${FORK_CONFIG_DIR}/mainnet/config/config.yaml
  sed -i 's/localhost/127.0.0.1/g' ${FORK_CONFIG_DIR}/mainnet/config/config.yaml
fi

echo "Fixing SSL permissions..."
chmod 755 -R ${FORK_CONFIG_DIR}/mainnet/config/ssl/ &> /dev/null
${FORK_CMD} init --fix-ssl-permissions > /dev/null

# Loop over provided list of key paths
echo "Importing keys..."
for k in ${keys//:/ }; do
  if [[ "${k}" == "persistent" ]]; then
    echo "Not touching key directories."
  elif [ -f ${k} ]; then
    echo "Adding key at path: ${k}"
    ${FORK_CMD} keys add -f ${k} > /dev/null
  else
    echo "Skipping 'chia keys add' as no file found at: ${k}"
  fi
done

# Loop over provided list of completed plot directories
IFS=':' read -r -a array <<< "$plots_dir"
joined=$(printf ", %s" "${array[@]}")
echo "Adding plot directories at: ${joined:1}"
for p in ${plots_dir//:/ }; do
  ${FORK_CMD} plots add -d ${p}
done

# Start services based on mode selected. Default is 'fullnode'
if [[ ${mode} == 'fullnode' ]]; then
  ${FORK_CMD} start farmer
elif [[ ${mode} =~ ^farmer.* ]]; then
  ${FORK_CMD} start farmer-only
elif [[ ${mode} =~ ^harvester.* ]]; then
  if [[ -z ${farmer_address} || -z ${farmer_port} ]]; then
    echo "A farmer peer address and port are required."
    exit 1
  else
    if [ ! -f ${FORK_CONFIG_DIR}/farmer_ca/chia_ca.crt ]; then
      mkdir -p ${FORK_CONFIG_DIR}/farmer_ca
      response=$(curl --write-out '%{http_code}' --silent http://${farmer_address}:8927/certificates/?type=${blockchains} --output /tmp/certs.zip)
      if [ $response == '200' ]; then
        unzip /tmp/certs.zip -d ${FORK_CONFIG_DIR}/farmer_ca
      else
        echo "Certificates response of ${response} from http://${farmer_address}:8927/certificates/?type=chia.  Try clicking 'New Worker' button on 'Workers' page first."
      fi
      rm -f /tmp/certs.zip
    fi
    if [ -f ${FORK_CONFIG_DIR}/farmer_ca/chia_ca.crt ]; then
      ${FORK_CMD} init -c ${FORK_CONFIG_DIR}/farmer_ca 2>&1 > ${FORK_CONFIG_DIR}/mainnet/log/init.log
      chmod 755 -R ${FORK_CONFIG_DIR}/mainnet/config/ssl/ &> /dev/null
      ${FORK_CMD} init --fix-ssl-permissions > /dev/null
    else
      echo "Did not find your farmer's certificates within /root/.chia/farmer_ca."
      echo "See: https://github.com/guydavis/machinaris/wiki/Workers#harvester"
    fi
    ${FORK_CMD} configure --set-farmer-peer ${farmer_address}:${farmer_port}
    ${FORK_CMD} configure --enable-upnp false
    ${FORK_CMD} start harvester -r
  fi
elif [[ ${mode} == 'plotter' ]]; then
    echo "Starting in Plotter-only mode.  Run Plotman from either CLI or WebUI."
fi
