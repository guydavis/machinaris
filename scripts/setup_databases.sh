#!/bin/bash
#
# Create the sqlite databases and tables
#

echo 'Creating database for Machinaris...'
mkdir -p /root/.chia/machinaris/dbs
cd /root/.chia/machinaris/dbs
sqlite3 machinaris.db <<EOF
CREATE TABLE stats (id INTEGER PRIMARY KEY, type TEXT, name TEXT, value REAL, unit TEXT, created_at TEXT);
CREATE TRIGGER stats_on_insert AFTER INSERT ON stats
 BEGIN
  UPDATE stats SET created_at = datetime('now') WHERE id = NEW.id;
 END;
EOF

echo 'Creating database for Chiadog...'
mkdir -p /root/.chia/chiadog/dbs
cd /root/.chia/chiadog/dbs
sqlite3 chiadog.db <<EOF
CREATE TABLE notifications (id INTEGER PRIMARY KEY, priority TEXT, service TEXT, message TEXT, created_at TEXT);
CREATE TRIGGER notifications_on_insert AFTER INSERT ON notifications
 BEGIN
  UPDATE notifications SET created_at = datetime('now') WHERE id = NEW.id;
 END;
EOF