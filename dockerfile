# Extend the official Chia docker image
# https://github.com/orgs/chia-network/packages/container/package/chia
FROM ghcr.io/chia-network/chia:latest

EXPOSE 8555
EXPOSE 8444

ENV keys="generate"
ENV harvester="false"
ENV farmer="false"
ENV plots_dir="/plots"
ENV farmer_address="null"
ENV farmer_port="null"
ENV testnet="false"
ENV full_node_port="null"

COPY ./swar /root/

RUN ls -al /root/ && ls -al /root/swar/ && /chia-blockchain/venv/bin/pip3 install /root/swar/requirements.txt

# Use entrypoint from official Chia docker image
ENTRYPOINT ["bash", "./entrypoint.sh"]
