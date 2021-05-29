# set ubuntu release version
ARG UBUNTU_VER="focal"

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
		python3.8-distutils \
		python3.8-venv \
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

# copy local files
COPY . /machinaris/

# set workdir
WORKDIR /chia-blockchain

# install Chia using official Chia Blockchain binaries
# Only if PATCH_CHIAPOS, patch for faster plotting, only on :chiapos image tag; see https://github.com/xrobau/chiapos
RUN \
	git clone --branch ${CHIA_BRANCH} https://github.com/Chia-Network/chia-blockchain.git /chia-blockchain \
	&& git submodule update --init mozilla-ca \
	&& chmod +x install.sh \
	&& /usr/bin/sh ./install.sh \
    &&  [[ -z "${PATCH_CHIAPOS}" ]] || ( \
		curl -o install_multithreaded_chiapos.sh https://gist.githubusercontent.com/SippieCup/8420c831ffcd74f4c4c3c756d1bda912/raw/45d44573b6aedf8ea47d8c485fb9eeeb342c53b4/install_multithreaded_chiapos.sh \
		&& chmod a+x install_multithreaded_chiapos.sh \
		&& ./install_multithreaded_chiapos.sh /chia-blockchain \
	) \
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
	. /machinaris/scripts/chiadog_install.sh \
	&& . /machinaris/scripts/plotman_install.sh \
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

# ports
EXPOSE 8555
EXPOSE 8444
EXPOSE 8926

WORKDIR /chia-blockchain
ENTRYPOINT ["bash", "./entrypoint.sh"]
