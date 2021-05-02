# Extend the official Chia docker image
# https://github.com/orgs/chia-network/packages/container/package/chia
FROM ghcr.io/chia-network/chia:latest

EXPOSE 8555
EXPOSE 8444
EXPOSE 8080

ENV keys="generate"
ENV harvester="false"
ENV farmer="false"
ENV plots_dir="/plots"
ENV farmer_address="null"
ENV farmer_port="null"
ENV testnet="false"
ENV full_node_port="null"

# Run Machinaris web frontend instead of final wait loop in parent image.
RUN "sed -i -e 's/while true.*/python3 -m http.server/g' entrypoint.sh"

ENTRYPOINT ["bash", "./entrypoint.sh"]
