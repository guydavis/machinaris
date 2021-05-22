
FROM ubuntu:latest

EXPOSE 8555
EXPOSE 8444
EXPOSE 8926

# Provide a colon-separated list of in-container paths to your mnemonic keys
ENV keys="/root/.chia/mnemonic.txt"  
# Provide a colon-separated list of in-container paths to your completed plots
ENV plots_dir="/plots"
# One of fullnode, plotter, farmer, or harvester. Default is fullnode
ENV mode="fullnode" 
# If mode=harvester, this is host and port the harvester will your farmer
ENV farmer_address="null"
ENV farmer_port="null"
# Only set true if using Chia's old test for testing only, default uses mainnet
ENV testnet="false"

ENV PATH="${PATH}:/chia-blockchain/venv/bin"
ENV TZ=Etc/UTC
ENV FLASK_ENV=production
ENV FLASK_APP=/machinaris/main.py
ENV XDG_CONFIG_HOME=/root/.chia

# Base install of official Chia binaries at given branch
ARG CHIA_BRANCH
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
   DEBIAN_FRONTEND=noninteractive apt-get install -y curl jq python3 \
   ansible tar bash ca-certificates git openssl unzip wget python3-pip \
   sudo acl build-essential python3-dev python3.8-venv python3.8-distutils \
   apt nfs-common python-is-python3 vim tzdata sqlite3
RUN echo "Cloning ${CHIA_BRANCH}"
RUN git clone --branch ${CHIA_BRANCH} https://github.com/Chia-Network/chia-blockchain.git \
   && cd chia-blockchain \
   && git submodule update --init mozilla-ca \
   && chmod +x install.sh \
   && /usr/bin/sh ./install.sh

# Now install additional tools such as Plotman, Chiadog, and Machinaris
COPY . /machinaris/
RUN . /machinaris/scripts/chiadog_install.sh && \
   /chia-blockchain/venv/bin/pip3 install git+https://github.com/ericaltendorf/plotman@main && \
   venv/bin/pip3 install -r /machinaris/requirements.txt && \
   cp -f /machinaris/entrypoint.sh /chia-blockchain/ && \
   chmod 755 /machinaris/start.sh /chia-blockchain/entrypoint.sh 

WORKDIR /chia-blockchain
ENTRYPOINT ["bash", "./entrypoint.sh"]
