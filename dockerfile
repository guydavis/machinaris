# set ubuntu release version
ARG UBUNTU_VER="hirsute"

######## packages stage ###########
FROM ubuntu:${UBUNTU_VER} as package_stage

ARG DEBIAN_FRONTEND=noninteractive

# install build packages
RUN \
	apt-get update \
	&& apt-get install -y \
		acl \
		ansible \
		apt \
		bash \
		bc \
		build-essential \
		ca-certificates \
		curl \
		git \
		jq \
		nfs-common \
		openssl \
		python3 \
		python3.9-distutils \
		python3.9-venv \
		python3-dev \
		python3-pip \
		python-is-python3 \
		sqlite3 \
		sudo \
		tar \
		tzdata \
		unzip \
		vim \
		wget \
		cmake \
		rsync \
		libsodium-dev \
		g++ \
		iputils-ping \
	\
# cleanup apt cache
	\
	&& rm -rf \
		/tmp/* \
		/var/lib/apt/lists/* \
		/var/tmp/*

######## build/runtime stage #########
FROM package_stage
# Base install of official Chia binaries at the given branch
ARG CHIA_BRANCH
ARG PATCH_CHIAPOS

# copy local files
COPY . /machinaris/

# set workdir
WORKDIR /chia-blockchain

# install Chia using official Chia Blockchain binaries
RUN \
	git clone --branch ${CHIA_BRANCH}  --single-branch https://github.com/Chia-Network/chia-blockchain.git /chia-blockchain \
	&& git submodule update --init mozilla-ca \
	&& chmod +x install.sh \
	&& /usr/bin/sh ./install.sh \
	\
# cleanup apt and pip caches
	\
	&& rm -rf \
		/root/.cache \
		/tmp/* \
		/var/lib/apt/lists/* \
		/var/tmp/*
# install additional tools such as Plotman, Chiadog, and Machinaris
RUN \
       /usr/bin/bash /machinaris/scripts/patch_chiapos.sh ${PATCH_CHIAPOS} \
	&& . /machinaris/scripts/chiadog_install.sh \
	&& . /machinaris/scripts/plotman_install.sh \
	&& . /machinaris/scripts/madmax_install.sh \
	&& . /machinaris/scripts/machinaris_install.sh \
	\
# cleanup apt and pip caches
	\
	&& rm -rf \
		/root/.cache \
		/tmp/* \
		/var/lib/apt/lists/* \
		/var/tmp/*

# Provide a colon-separated list of in-container paths to your mnemonic keys
ENV keys="/root/.chia/mnemonic.txt"  
# Provide a colon-separated list of in-container paths to your completed plots
ENV plots_dir="/plots"
# One of fullnode, farmer, harvester, plotter, farmer+plotter, harvester+plotter. Default is fullnode
ENV mode="fullnode" 
# If mode=plotter, optional 2 public keys will be set in your plotman.yaml
ENV farmer_pk="null"
ENV pool_pk="null"
# If mode=harvester, required for host and port the harvester will your farmer
ENV farmer_address="null"
ENV farmer_port="8447"
# Only set true if using Chia's old test for testing only, default uses mainnet
ENV testnet="false"
# Can override the location of default settings for api and web servers.
ENV API_SETTINGS_FILE='/root/.chia/machinaris/config/api.cfg'
ENV WEB_SETTINGS_FILE='/root/.chia/machinaris/config/web.cfg'
# Local network hostname of a Machinaris controller - localhost when standalone
ENV controller_host="localhost"
ENV controller_web_port=8926
ENV controller_api_port=8927

ENV PATH="${PATH}:/chia-blockchain/venv/bin"
ENV TZ=Etc/UTC
ENV FLASK_ENV=production
ENV FLASK_APP=/machinaris/main.py
ENV XDG_CONFIG_HOME=/root/.chia
ENV AUTO_PLOT=false

VOLUME [ "/id_rsa" ]

# ports
EXPOSE 8555
EXPOSE 8444
EXPOSE 8926
EXPOSE 8927

WORKDIR /chia-blockchain
ENTRYPOINT ["bash", "./entrypoint.sh"]
