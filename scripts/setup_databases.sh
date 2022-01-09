#!/bin/bash
#
# Use flask-migrate to manage the different sqlite dbs
#

mkdir -p /root/.chia/machinaris/logs
mkdir -p /root/.chia/machinaris/dbs

# Optional reset parameter will remove broken DBs, allowing fresh setup of status
if [[ $1 == "reset" ]]; then
    mv /root/.chia/machinaris/dbs/machinaris.db /root/.chia/machinaris/dbs/machinaris.db.bak
    mv /root/.chia/machinaris/dbs/stats.db /root/.chia/machinaris/dbs/stats.db.bak
fi

# Perform database migration, if any
cd /machinaris/api
FLASK_APP=__init__.py flask db upgrade >> /root/.chia/machinaris/logs/migration.log 2>&1 
