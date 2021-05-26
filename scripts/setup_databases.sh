#!/bin/bash
#
# Create the sqlite databases and tables
#

# stat_plots_count
# stat_plots_size
# stat_total_chia
# stat_netspace_size
# stat_time_to_win

# Later
# stat_plots_free_total
# stat_plots_free_disk
# stat_plotting_free_total
# stat_plotting_free_disk

mkdir -p /root/.chia/machinaris/dbs
pushd /root/.chia/machinaris/dbs
rm -f machinaris.db # Temporarily delete old db 
if [ ! -f stats.db ]; then
    echo 'Creating database for Machinaris...'
    sqlite3 stats.db <<EOF

CREATE TABLE IF NOT EXISTS stat_plot_count (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TRIGGER stat_plot_count_on_insert AFTER INSERT ON stat_plot_count
 BEGIN
  UPDATE stat_plot_count SET created_at = datetime('now') WHERE id = NEW.id;
 END;

CREATE TABLE stat_plots_size (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TRIGGER stat_plots_size_on_insert AFTER INSERT ON stat_plots_size
 BEGIN
  UPDATE stat_plots_size SET created_at = datetime('now') WHERE id = NEW.id;
 END;

CREATE TABLE stat_total_chia (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TRIGGER stat_total_chia_on_insert AFTER INSERT ON stat_total_chia
 BEGIN
  UPDATE stat_total_chia SET created_at = datetime('now') WHERE id = NEW.id;
 END;

CREATE TABLE stat_netspace_size (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TRIGGER stat_netspace_size_on_insert AFTER INSERT ON stat_netspace_size
 BEGIN
  UPDATE stat_netspace_size SET created_at = datetime('now') WHERE id = NEW.id;
 END;

CREATE TABLE stat_time_to_win (id INTEGER PRIMARY KEY, value REAL, created_at TEXT);
CREATE TRIGGER stat_time_to_win_on_insert AFTER INSERT ON stat_time_to_win
 BEGIN
  UPDATE stat_time_to_win SET created_at = datetime('now') WHERE id = NEW.id;
 END;

EOF
    chmod 666 /root/.chia/machinaris/dbs/stats.db
fi
popd

mkdir -p /root/.chia/chiadog/dbs
pushd /root/.chia/chiadog/dbs
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
popd