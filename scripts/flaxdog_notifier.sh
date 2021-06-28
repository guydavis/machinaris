#!/bin/bash
#
# Record notifications from Chiadog to event files for parsing by Machinaris
#

event_priority_name="$1"
event_service_name="$2"
event_message="$3"

cd /root/.chia/chiadog/dbs
sqlite3 chiadog.db <<EOF
INSERT INTO notification (priority,service,message,created_at) VALUES ('${event_priority_name//\'/\'\'}','${event_service_name//\'/\'\'}','${event_message//\'/\'\'}', strftime('%Y-%m-%d %H:%M:%S','now'));
EOF
