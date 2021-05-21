
# Extend the official Chia docker image
# https://github.com/orgs/chia-network/packages/container/package/chia
FROM ghcr.io/chia-network/chia:latest

EXPOSE 8555
EXPOSE 8444
EXPOSE 8926

ENV keys="/root/.chia/mnemonic.txt"
ENV mode="fullnode" 
ENV plots_dir="/plots"

ENV farmer_address="null"
ENV farmer_port="null"
ENV testnet="false"
ENV full_node_port="null"

ENV PATH="${PATH}:/chia-blockchain/venv/bin"
ENV TZ=Etc/UTC
ENV FLASK_ENV=production
ENV FLASK_APP=/machinaris/main.py
ENV XDG_CONFIG_HOME=/root/.chia

COPY . /machinaris/
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata && . /machinaris/patch_chia.txt && \
   /chia-blockchain/venv/bin/pip3 install git+https://github.com/ericaltendorf/plotman@main && \
   venv/bin/pip3 install -r /machinaris/requirements.txt && \
   cp -f /machinaris/entrypoint.sh /chia-blockchain/ && \
   chmod 755 /machinaris/start.sh /chia-blockchain/entrypoint.sh 

ENTRYPOINT ["bash", "./entrypoint.sh"]
