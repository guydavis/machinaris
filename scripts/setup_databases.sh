#!/bin/bash
#
# Use flask-migrate to manage the different sqlite dbs
#

mkdir -p /root/.chia/machinaris/logs
mkdir -p /root/.chia/machinaris/dbs
mkdir -p /root/.chia/chiadog/dbs

# If old databases not managed by flask-migrate yet
if [ ! -f /root/.chia/machinaris/dbs/.managed ] && [ -f /root/.chia/machinaris/dbs/stats.db ]; then
    cd /root/.chia/machinaris/dbs
    rm -f machinaris.db
    mv stats.db stats.db.old
fi
if [ ! -f /root/.chia/chiadog/dbs/.managed ] && [ -f /root/.chia/chiadog/dbs/chiadog.db ]; then
    cd /root/.chia/chiadog/dbs
    mv chiadog.db chiadog.db.old
fi

# Perform database migration, if any
cd /machinaris/api
FLASK_APP=__init__.py flask db upgrade >> /root/.chia/machinaris/logs/migration.log 2>&1 

# If old databases weren't managed by flask-migrate before, copy over old data
if [ ! -f /root/.chia/machinaris/dbs/.managed ] && [ -f /root/.chia/machinaris/dbs/stats.db.old ]; then
    sqlite3 /root/.chia/machinaris/dbs/stats.db.old <<EOF
    ATTACH DATABASE '/root/.chia/machinaris/dbs/stats.db' AS new_db;
    INSERT INTO new_db.stat_plots_disk_used SELECT * FROM stat_plots_disk_used;
    INSERT INTO new_db.stat_plotting_disk_used SELECT * FROM stat_plotting_disk_used;
    INSERT INTO new_db.stat_netspace_size SELECT * FROM stat_netspace_size;
    INSERT INTO new_db.stat_plots_size SELECT * FROM stat_plots_size;
    INSERT INTO new_db.stat_plotting_total_used SELECT * FROM stat_plotting_total_used;
    INSERT INTO new_db.stat_plot_count SELECT * FROM stat_plot_count;
    INSERT INTO new_db.stat_plots_total_used SELECT * FROM stat_plots_total_used;
    INSERT INTO new_db.stat_time_to_win SELECT * FROM stat_time_to_win;
    INSERT INTO new_db.stat_plots_disk_free SELECT * FROM stat_plots_disk_free;
    INSERT INTO new_db.stat_plotting_disk_free SELECT * FROM stat_plotting_disk_free;
    INSERT INTO new_db.stat_total_chia SELECT * FROM stat_total_chia;
EOF
fi
touch /root/.chia/machinaris/dbs/.managed

if [ ! -f /root/.chia/chiadog/dbs/.managed ] && [ -f /root/.chia/chiadog/dbs/chiadog.db.old ]; then
    sqlite3 /root/.chia/chiadog/dbs/chiadog.db.old <<EOF
    ATTACH DATABASE '/root/.chia/chiadog/dbs/chiadog.db' AS new_db;
    INSERT INTO new_db.notification SELECT * FROM notification;
EOF
fi
touch /root/.chia/chiadog/dbs/.managed
