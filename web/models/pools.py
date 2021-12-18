import json
import locale
import os
import re
import traceback

import datetime

from common.models.plotnfts import Plotnft
from web import app, db
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
                app.logger.info("Plotnfts.init(): Unable to find a worker with hostname '{0}'".format(plotnft.hostname))
                displayname = plotnft.hostname
            self.rows.append({ 
                'displayname': displayname, 
                'hostname': plotnft.hostname,
                'blockchain': plotnft.blockchain,
                'launcher_id': plotnft.launcher,
                'wallet_num': plotnft.wallet_num,
                'header': plotnft.header, 
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
                app.logger.info("Pools.init(): Unable to find a worker with hostname '{0}' for {1}".format(pool.hostname, pool.blockchain))
                displayname = pool.hostname
            launcher_id = pool.launcher_id
            plotnft = self.find_plotnft(plotnfts, launcher_id)
            pool_state = json.loads(pool.pool_state)
            if plotnft:
                status = self.extract_plotnft_value(plotnft, "Current state:")
                points_successful_last_24h = self.extract_plotnft_value(plotnft, "Percent Successful Points (24h)")
                num_plots = self.extract_plotnft_value(plotnft, "Number of plots:")
            else:
                status = "-"
                num_plots = '-'
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
                'num_plots': num_plots, 
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


class PoolConfigs():

    def __init__(self, blockchain, plotnfts, wallets):
        self.plotnfts = plotnfts
        if blockchain == 'chia':
            self.links = self.chia_links()
        elif blockchain == 'chives':
            self.links = self.chives_links()
        else:
            raise Exception("Unsupported blockchain for pooling: {0}".format(blockchain))
        self.warnings = self.get_warnings(blockchain, wallets)
        if len(self.warnings) == 0 and len(self.plotnfts) == 0:
            self.plotnfts.append(Plotnft(blockchain=blockchain, details=""))

    def chia_links(self):
        links = {}
        links['compare_pools'] = "https://chiapool.directory/"
        links['get_mojos'] = "https://faucet.chia.net/"
        return links

    def chives_links(self):
        links = {}
        links['compare_pools'] = "https://www.chivespool.com/"  # TODO Find a chives pool compare site...
        return links

    def get_warnings(self, blockchain, wallets):
        warnings = []
        for wallet in wallets:
            if not wallet.is_synced():
                warnings.append("{0} wallet ({1}) is not fully synced yet.  Please allow wallet time to complete syncing before changing Pooling settings.".format(blockchain.capitalize(), wallet.wallet_id()))
            if (blockchain == 'chia' and not wallet.has_few_mojos()):
                warnings.append("{0} wallet ({1}) has a zero balance.  Please request some mojos from a <a href='{2}' target='_blank'>faucet</a>, then try again hours later.".format(blockchain.capitalize(), wallet.wallet_id(), self.links['get_mojos']))
        return warnings
