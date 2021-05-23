
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
# If mode=plotter, optional 2 public keys will be set in your plotman.yaml
ENV farmer_pk="null"
ENV pool_pk="null"
# If mode=harvester, required for host and port the harvester will your farmer
ENV farmer_address="null"
ENV farmer_port="null"
# Only set true if using Chia's old test for testing only, default uses mainnet
ENV testnet="false"

ENV PATH="${PATH}:/chia-blockchain/venv/bin"
ENV TZ=Etc/UTC
ENV FLASK_ENV=production
ENV FLASK_APP=/machinaris/main.py
ENV XDG_CONFIG_HOME=/root/.chia

# Base install of official Chia binaries at the given branch
ARG CHIA_BRANCH
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
   DEBIAN_FRONTEND=noninteractive apt-get install -y curl jq python3 \
   ansible tar bash ca-certificates git openssl unzip wget python3-pip \
   sudo acl build-essential python3-dev python3.8-venv python3.8-distutils \
   apt nfs-common python-is-python3 vim tzdata sqlite3
RUN git clone --branch ${CHIA_BRANCH} https://github.com/Chia-Network/chia-blockchain.git \
   && cd chia-blockchain \
   && git submodule update --init mozilla-ca \
   && chmod +x install.sh \
   && /usr/bin/sh ./install.sh

# Now install additional tools such as Plotman, Chiadog, and Machinaris
COPY . /machinaris/
RUN . /machinaris/scripts/chiadog_install.sh && \
   . /machinaris/scripts/plotman_install.sh && \
   . /machinaris/scripts/machinaris_install.sh

WORKDIR /chia-blockchain
ENTRYPOINT ["bash", "./entrypoint.sh"]
