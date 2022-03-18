#!/bin/bash
#
# Use flask-migrate to manage the different sqlite dbs
#

mkdir -p /root/.chia/machinaris/logs
mkdir -p /root/.chia/machinaris/dbs
mkdir -p /root/.chia/machinaris/cache

if [[ $1 == "reset" ]]; then
    rm -f /root/.chia/machinaris/dbs/*.db
fi

# Perform database migration, if any
cd /machinaris/api
FLASK_APP=__init__.py flask db upgrade >> /root/.chia/machinaris/logs/migration.log 2>&1 
