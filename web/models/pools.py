import json
import locale
import os
import re
import traceback

import datetime

from flask_babel import _, lazy_gettext as _l
from common.models.plotnfts import Plotnft
from web import app, db
from web.actions import worker as w

class Plotnfts:

    def __init__(self, plotnfts):
        self.columns = ['hostname', 'details', 'updated_at']
        self.rows = []
        for plotnft in plotnfts:
            if plotnft.blockchain == 'gigahorse':
                continue  # Ignore these, use Chia instead.
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(plotnft.hostname))
                displayname = w.get_worker(plotnft.hostname).displayname
            except:
                app.logger.info("Plotnfts.init(): Unable to find a worker with hostname '{0}'".format(plotnft.hostname))
                displayname = plotnft.hostname
            plotnft_obj = { 
                'displayname': displayname, 
                'hostname': plotnft.hostname,
                'blockchain': plotnft.blockchain,
                'launcher_id': plotnft.launcher,
                'wallet_num': plotnft.wallet_num,
                'header': plotnft.header, 
                'details': plotnft.details, 
                'updated_at': plotnft.updated_at 
            }
            self.rows.append(plotnft_obj)
    
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
        self.blockchains = {}
        for pool in pools:
            if pool.blockchain == 'gigahorse':
                continue  # Ignore these, use Chia instead.
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
            errors = self.extract_unique_errors(pool_state)
            pool_obj = { 
                'displayname': displayname, 
                'hostname': pool.hostname,
                'launcher_id': pool.launcher_id, 
                'login_link': pool.login_link,
                'num_plots': num_plots, 
                'blockchain': pool.blockchain, 
                'pool_state': pool_state,
                'updated_at': pool.updated_at,
                'status': status,
                'errors': errors,
                'points_successful_last_24h': points_successful_last_24h,
            }
            if pool.blockchain in self.blockchains:
                blockchain_pools = self.blockchains[pool.blockchain]
            else:
                blockchain_pools = []
                self.blockchains[pool.blockchain] = blockchain_pools
            blockchain_pools.append(pool_obj)
    
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
    
    def extract_unique_errors(self, pool_state):
        errors = []
        if 'pool_errors_24h' in pool_state:
            for error in pool_state['pool_errors_24h']:
                if not error['error_message'] in errors:
                    errors.append(error['error_message'])
        return errors

class PartialsChartData:
    
    # select count(*), substr(created_at, 0,14) as hr from partials where blockchain = 'chia' group by hr order by hr;
    def __init__(self, partials):
        self.labels = []
        label_index_by_hour = {}
        for i in range(1,25):
            start_time = datetime.datetime.now().replace(microsecond=0, second=0, minute=0) - datetime.timedelta(hours=24-i)
            self.labels.append(start_time.strftime("%I %p"))
            label_index_by_hour[start_time.strftime("%H")] = len(self.labels) - 1
            #app.logger.info("At {0} is label: {1}".format((len(self.labels) - 1), start_time.strftime("%I %p")))
        self.data = {}
        for partial in partials:
            created_at = partial.created_at
            pool_launcher = partial.pool_url.replace('https://', '') + ' (' + partial.launcher_id[:8] + '...)'
            if not pool_launcher in self.data:
                self.data[pool_launcher] = [0] * 24 # Initialize as list of zeros
            dataset = self.data[pool_launcher]
            partial_hour_at = created_at[11:13]
            #app.logger.info("{0}: partial_hour_at={1} -> slot {2}".format(created_at, partial_hour_at, label_index_by_hour[partial_hour_at]))
            dataset[label_index_by_hour[partial_hour_at]] += 1
            
class PoolConfigs():

    def __init__(self, blockchain, plotnfts, wallets):
        self.plotnfts = plotnfts
        if blockchain in ['chia', 'gigahorse']:
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
        links['compare_pools'] = "https://www.chivespool.com/"  # TODO Find a chives pool compare site... any other pools?
        links['get_mojos'] = "https://faucet.chivescoin.org/" 
        return links

    def get_warnings(self, blockchain, wallets):
        warnings = []
        for wallet in wallets:
            if not wallet.is_synced():
                warnings.append(_("%(blockchain)s wallet (%(wallet_id)s) is not fully synced yet.  Please allow wallet time to complete syncing before changing Pooling settings.", 
                    blockchain=blockchain.capitalize(), wallet_id=wallet.wallet_id()))
            if not wallet.has_few_mojos():
                warnings.append(_("%(blockchain)s wallet (%(wallet_id)s) has a zero balance.  Please request some mojos from a %(link_open)sfaucet%(link_close)s for the first wallet address on the Keys page, then try again later.",
                    blockchain=blockchain.capitalize(), wallet_id=wallet.wallet_id(), 
                    link_open="<a class='text-white' href='{0}' target='_blank'>".format(self.links['get_mojos']), 
                    link_close="</a>"))
        return warnings
