#!/bin/bash
#
# Record notifications from Chiadog to event files for parsing by Machinaris
#

event_priority_name="$1"
event_service_name="$2"
event_message="$3"
hostname="$(hostname -s)"
now="$(date +'%Y-%m-%d %H:%M:%S')"
unique_id="${hostname}_chia_${now}"
echo "Creating alert ${hostname}_chia_${now} ${event_service_name} ${event_priority_name}: ${event_message}"

cd /root/.chia/machinaris/dbs
sqlite3 -cmd '.timeout 5000' machinaris.db <<EOF
INSERT INTO alerts (unique_id,hostname,blockchain,priority,service,message,created_at) VALUES ('${unique_id}', '${hostname}', 'chia','${event_priority_name//\'/\'\'}','${event_service_name//\'/\'\'}','${event_message//\'/\'\'}', '${now}');
EOF
