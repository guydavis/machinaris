#!/bin/bash
#
# Create the sqlite databases and tables
#

mkdir -p /root/.chia/machinaris/dbs
cd /root/.chia/machinaris/dbs
if [ ! -f stats.db ]; then
    echo 'Creating database for Machinaris...'
    sqlite3 stats.db <<EOF
CREATE TABLE stat_plot_count (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TABLE stat_plots_size (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TABLE stat_total_chia (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TABLE stat_netspace_size (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TABLE stat_time_to_win (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TABLE stat_plots_total_used (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TABLE stat_plots_disk_used (id INTEGER PRIMARY KEY, hostname TEXT, path TEXT, value REAL, created_at TEXT);
CREATE TABLE stat_plots_disk_free (id INTEGER PRIMARY KEY, hostname TEXT, path TEXT, value REAL, created_at TEXT);
CREATE TABLE stat_plotting_total_used (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TABLE stat_plotting_disk_used (id INTEGER PRIMARY KEY, hostname TEXT, path TEXT, value REAL, created_at TEXT);
CREATE TABLE stat_plotting_disk_free (id INTEGER PRIMARY KEY, hostname TEXT, path TEXT, value REAL, created_at TEXT);
EOF
    chmod 666 /root/.chia/machinaris/dbs/stats.db
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
