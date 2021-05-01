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

# Set default Plotman config location to /root/.chia/plotman in container
ENV XDG_CONFIG_HOME=/root/.chia

# Execute Plotman install via pip3 and use a customized config
# https://github.com/ericaltendorf/plotman
RUN /chia-blockchain/venv/bin/pip3 install --force-reinstall git+https://github.com/ericaltendorf/plotman@main && mkdir -p /root/.chia/plotman/
ADD ./plotman.yaml /root/.chia/plotman/plotman.yaml

# Use entrypoint from official Chia docker image
ENTRYPOINT ["bash", "./entrypoint.sh"]
