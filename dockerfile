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

# Execute Plotman install via pip3
# https://github.com/ericaltendorf/plotman
RUN /chia-blockchain/venv/bin/activate && /chia-blockchain/venv/bin/pip3 install --force-reinstall git+https://github.com/ericaltendorf/plotman@main 

# Use entrypoint from official Chia docker image
ENTRYPOINT ["bash", "./entrypoint.sh"]
