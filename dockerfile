
# Extend the official Chia docker image
# https://github.com/orgs/chia-network/packages/container/package/chia
FROM ghcr.io/chia-network/chia:latest

EXPOSE 8555
EXPOSE 8444
EXPOSE 5000

ENV keys="generate"
ENV harvester="false"
ENV farmer="false"
ENV plots_dir="/plots"
ENV farmer_address="null"
ENV farmer_port="null"
ENV testnet="false"
ENV full_node_port="null"

ENV PATH="${PATH}:/chia-blockchain/venv/bin"

ENV FLASK_ENV=development
ENV FLASK_APP=/machinaris/main.py

ENV XDG_CONFIG_HOME=/root/.chia
RUN /chia-blockchain/venv/bin/pip3 install --force-reinstall git+https://github.com/ericaltendorf/plotman@main

COPY . /machinaris/
RUN venv/bin/pip3 install -r /machinaris/requirements.txt && \
   chmod 755 /machinaris/start.sh && \
   sed -i -e "s/while true/\/machinaris\/start.sh; while true/g" entrypoint.sh

ENTRYPOINT ["bash", "./entrypoint.sh"]
