#!/bin/bash
#
# Create the sqlite databases and tables
#

mkdir -p /root/.chia/machinaris/dbs
cd /root/.chia/machinaris/dbs
if [ ! -f machinaris.db ]; then
    echo 'Creating database for Machinaris...'
    sqlite3 machinaris.db <<EOF
CREATE TABLE stat (id INTEGER PRIMARY KEY, type TEXT, name TEXT, value REAL, unit TEXT, created_at TEXT);
CREATE TRIGGER stat_on_insert AFTER INSERT ON stat
 BEGIN
  UPDATE stat SET created_at = datetime('now') WHERE id = NEW.id;
 END;
EOF
    chmod 666 /root/.chia/machinaris/dbs/machinaris.db
fi

mkdir -p /root/.chia/chiadog/dbs
cd /root/.chia/chiadog/dbs
if [ ! -f chiadog.db ]; then
    echo 'Creating database for Chiadog...'
    sqlite3 chiadog.db <<EOF
CREATE TABLE notification (id INTEGER PRIMARY KEY, priority TEXT, service TEXT, message TEXT, created_at TEXT);
CREATE TRIGGER notification_on_insert AFTER INSERT ON notification
 BEGIN
  UPDATE notification SET created_at = datetime('now') WHERE id = NEW.id;
 END;
EOF
    chmod 666 /root/.chia/chiadog/dbs/chiadog.db
fi