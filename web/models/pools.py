import json
import locale
import os
import re
import traceback

import datetime

from web import app
from web.actions import worker as w

class Plotnfts:

    def __init__(self, plotnfts):
        self.columns = ['hostname', 'details', 'updated_at']
        self.rows = []
        for plotnft in plotnfts:
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(plotnft.hostname))
                displayname = w.get_worker(plotnft.hostname).displayname
            except:
                traceback.print_exc()
                app.logger.info("Unable to find a worker with hostname '{0}'".format(plotnft.hostname))
                displayname = plotnft.hostname
            self.rows.append({ 
                'displayname': displayname, 
                'hostname': plotnft.hostname,
                'blockchain': plotnft.blockchain, 
                'details': plotnft.details, 
                'updated_at': plotnft.updated_at })
    
    def get_current_pool_url(self):
        pool_url = None
        for row in self.rows:
            for line in row['details'].split('\n'):
                if "Current pool URL:" in line:
                    pool_url = line[len("Current pool URL:"):].strip()
                elif "Target state: SELF_POOLING" in line:
                    return None  # Switching back to self-pooling, no pool_url
        return pool_url

class Pools:

    def __init__(self, pools, plotnfts):
        self.columns = ['hostname', 'blockchain', 'pool_state', 'updated_at']
        self.rows = []
        for pool in pools:
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(pool.hostname))
                displayname = w.get_worker(pool.hostname, pool.blockchain).displayname
            except:
                traceback.print_exc()
                app.logger.info("Unable to find a worker with hostname '{0}' for {1}".format(pool.hostname, pool.blockchain))
                displayname = pool.hostname
            launcher_id = pool.launcher_id
            plotnft = self.find_plotnft(plotnfts, launcher_id)
            pool_state = json.loads(pool.pool_state)
            if plotnft:
                status = self.extract_plotnft_value(plotnft, "Current state:")
                points_successful_last_24h = self.extract_plotnft_value(plotnft, "Percent Successful Points (24h)")
            else:
                status = "-"
                pool_errors_24h = len(pool_state['pool_errors_24h'])
                points_found_24h = len(pool_state['points_found_24h'])
                if points_found_24h == 0:
                    points_successful_last_24h = "0"
                else:
                    points_successful_last_24h = "%.2f"% ( (points_found_24h - pool_errors_24h) / points_found_24h * 100)
            self.rows.append({ 
                'displayname': displayname, 
                'hostname': pool.hostname,
                'launcher_id': pool.launcher_id, 
                'login_link': pool.login_link, 
                'blockchain': pool.blockchain, 
                'pool_state': pool_state,
                'updated_at': pool.updated_at,
                'status': status,
                'points_successful_last_24h': points_successful_last_24h
            })
    
    def find_plotnft(self, plotnfts, launcher_id):
        for plotnft in plotnfts:
            if launcher_id in plotnft.details:
                return plotnft
        return None

    def extract_plotnft_value(self, plotnft, key):
        for line in plotnft.details.splitlines():
            if line.startswith(key):
                return line[line.index(':')+1:].strip()
        return None
