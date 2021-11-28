import json
import locale
import os
import re
import traceback

import datetime

from web import app
from web.actions import worker as w
from common.config.globals import CURRENCY_SYMBOLS
from common.utils import converters

# Treat *.plot files smaller than this as in-transit (copying) so don't count them
MINIMUM_K32_PLOT_SIZE_BYTES = 100 * 1024 * 1024

PLOT_TABLE_COLUMNS = ['worker', 'fork', 'plot_id',  'dir', 'plot', 'type', 'create_date', 'size', 'c', 'a' ]

class FarmSummary:

    def __init__(self, farm_recs, wallet_recs):
        self.farms = {}
        chives_farm_recs = []
        wallets = Wallets(wallet_recs)
        for farm_rec in farm_recs: 
            if 'chives' == farm_rec.blockchain:  # Chives sends from both harvesters and fullnodes
                chives_farm_recs.append(farm_rec) # Must later combine them together for single summary
            elif farm_rec.mode == "fullnode":
                try:
                    app.logger.debug("Found worker with hostname '{0}'".format(farm_rec.hostname))
                    wkr = w.get_worker(farm_rec.hostname, farm_rec.blockchain)
                    displayname = wkr.displayname
                    connection_status = wkr.connection_status()
                except Exception as ex:
                    app.logger.info(str(ex))
                    app.logger.info("Unable to find a worker with hostname '{0}' and blockchain '{1}'".format(farm_rec.hostname, farm_rec.blockchain))
                    displayname = farm_rec.hostname
                    connection_status = None
                try:
                    wallet_balance = wallets.sum_wallet_balance(farm_rec.hostname, farm_rec.blockchain)
                except: 
                    wallet_balance = '?'
                if farm_rec.total_coins:
                    total_coins = converters.round_balance(farm_rec.total_coins)
                else:
                    total_coins = converters.round_balance(0)
                farm = {
                    "plot_count": int(farm_rec.plot_count),
                    "plots_size": farm_rec.plots_size,
                    "plots_display_size": converters.gib_to_fmt(farm_rec.plots_size),
                    "status": farm_rec.status,
                    "display_status": self.status_if_responding(displayname, farm_rec.blockchain, connection_status, farm_rec.status),
                    "total_coins": total_coins,
                    "wallet_balance": wallet_balance,
                    "currency_symbol": CURRENCY_SYMBOLS[farm_rec.blockchain],
                    "netspace_display_size": '?' if not farm_rec.netspace_size else converters.gib_to_fmt(farm_rec.netspace_size),
                    "netspace_size": farm_rec.netspace_size,
                    "expected_time_to_win": farm_rec.expected_time_to_win,
                }
                if not farm_rec.blockchain in self.farms:
                    self.farms[farm_rec.blockchain] = farm
                else:
                    app.logger.info("Discarding duplicate fullnode blockchain status from {0} - {1}".format(farm_rec.hostname, farm_rec.blockchain))    
            else:
                app.logger.info("Stale farm status for {0} - {1}".format(farm_rec.hostname, farm_rec.blockchain))
        # Now combine Chives farm records from fullnodes and harvesters
        self.combine_chives_recs_into_summary(chives_farm_recs, wallet_recs)
        if len(self.farms) == 0:  # Handle completely missing farm summary info 
            self.farms['chia'] = {} # with empty chia farm

    def combine_chives_recs_into_summary(self, chives_farm_recs, wallet_recs):
        plot_count = 0
        plots_size = 0
        fullnode = None
        wallet_balance = '?'
        displayname = '?'
        connection_status = '?'
        wallets = Wallets(wallet_recs)
        for farm_rec in chives_farm_recs:
            plot_count += int(farm_rec.plot_count)
            plots_size += farm_rec.plots_size
            if farm_rec.mode == 'fullnode':
                fullnode = farm_rec
                try:
                    app.logger.debug("Found worker with hostname '{0}'".format(farm_rec.hostname))
                    wkr = w.get_worker(farm_rec.hostname, 'chives')
                    displayname = wkr.displayname
                    connection_status = wkr.connection_status()
                except Exception as ex:
                    app.logger.info(str(ex))
                    app.logger.info("Unable to find a worker with hostname '{0}' and blockchain '{1}'".format(farm_rec.hostname, 'chives'))
                    displayname = farm_rec.hostname
                    connection_status = None
                try:
                    wallet_balance = wallets.sum_wallet_balance(farm_rec.hostname, 'chives')
                except Exception as ex: 
                    app.logger.info("Failed to sum Chives wallet balances.".format(str(ex)))
        if fullnode:
            if len(chives_farm_recs) > 0:
                total_etw = self.calc_entire_farm_etw(fullnode.plots_size, fullnode.expected_time_to_win, plots_size)
            else:
                total_etw = fullnode.expected_time_to_win
            farm = {
                "plot_count": int(plot_count),
                "plots_size": plots_size,
                "plots_display_size": converters.gib_to_fmt(plots_size),
                "status": fullnode.status,
                "display_status": self.status_if_responding(displayname, 'chives', connection_status, fullnode.status),
                "total_coins": '0.0' if not fullnode.total_coins else round(fullnode.total_coins, 6),
                "wallet_balance": wallet_balance,
                "currency_symbol": CURRENCY_SYMBOLS['chives'],
                "netspace_display_size": '?' if not fullnode.netspace_size else converters.gib_to_fmt(fullnode.netspace_size),
                "netspace_size": fullnode.netspace_size,
                "expected_time_to_win": total_etw,
            }
            self.farms['chives'] = farm
        elif len(chives_farm_recs) > 0:
            app.logger.error("Found {0} chives farm summary records, but none were the fullnode.".format(len(chives_farm_recs)))

    # Only needed for older Chives code-base which reports ETW of plots only on fullnode
    def calc_entire_farm_etw(self, fullnode_plots_size, expected_time_to_win, total_farm_plots_size):
        try:
            fullnode_etw_mins = converters.etw_to_minutes(expected_time_to_win)
            total_farm_etw_mins = (fullnode_plots_size / total_farm_plots_size) * fullnode_etw_mins
            return converters.format_minutes(int(total_farm_etw_mins))
        except Exception as ex:
            app.logger.debug("Failed to calculate ETW for entire farm due to: {0}".format(str(ex)))
            return "-"

    def status_if_responding(self, displayname, blockchain, connection_status, last_status):
        if connection_status == 'Responding':
            return "Active" if last_status == "Farming" else last_status
        app.logger.info("Oops! {0} ({1}) had connection_success: {2}".format(displayname, blockchain, connection_status))
        return "Offline"

class FarmPlots:

    def __init__(self, plots):
        self.columns = PLOT_TABLE_COLUMNS
        self.rows = []
        for plot in plots:
            self.rows.append([
                plot.displayname,  
                plot.blockchain, 
                plot.plot_id, 
                plot.dir,  
                app.jinja_env.filters['plotnameshortener'](plot.file),
                plot.type if plot.type else "", 
                plot.created_at, 
                app.jinja_env.filters['bytesfilter'](plot.size),
                self.get_check_cell_value(plot.plot_id, plot.plot_check),
                self.get_analzye_cell_value(plot.plot_id, plot.plot_analyze),
            ])

    def get_analzye_cell_value(self, plot_id, plot_analyze):
        if plot_analyze and plot_analyze != '-':
            return "{0} | {1}".format(plot_analyze, plot_id)
        return ""

    def get_check_cell_value(self, plot_id, plot_check):
        if plot_check and plot_check != '-':
            return "{0} | {1}".format(plot_check, plot_id)
        return ""


class ChallengesChartData:

    def __init__(self, challenges):
        self.labels = []
        datasets = {}
        for challenge in challenges:
            created_at = challenge.created_at.replace(' ', 'T')
            if not created_at in self.labels:
                self.labels.append(created_at)
            host_chain = challenge.hostname
            if not host_chain in datasets:
                datasets[host_chain] = {}
            dataset = datasets[host_chain]
            dataset[created_at] = float(challenge.time_taken.split()[0]) # Drop off the 'secs'
        # Now build a sparse array with null otherwise
        self.data = {}
        for key in datasets.keys():
            self.data[key] = [] 
        for label in self.labels:
            for key in datasets.keys():
                if label in datasets[key]:
                    self.data[key].append(datasets[key][label])
                else:
                    self.data[key].append('null') # Javascript null

class Wallets:

    def __init__(self, wallets, cold_wallet_addresses={}):
        self.wallets = wallets
        self.columns = ['hostname', 'details', 'updated_at']
        self.rows = []
        self.cold_wallet_addresses = cold_wallet_addresses
        for wallet in wallets:
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(wallet.hostname))
                displayname = w.get_worker(wallet.hostname, wallet.blockchain).displayname
            except:
                app.logger.info("Unable to find a worker with hostname '{0}'".format(wallet.hostname))
                displayname = wallet.hostname
            hot_balance = self.sum_wallet_balance(wallet.hostname, wallet.blockchain, False)
            cold_balance = wallet.cold_balance
            try:
                total_balance = converters.round_balance(float(hot_balance) + float(cold_balance))
            except:
                total_balance = hot_balance
            self.rows.append({ 
                'displayname': displayname, 
                'hostname': wallet.hostname,
                'blockchain': wallet.blockchain, 
                'details': wallet.details, 
                'hot_balance': hot_balance,
                'cold_balance': cold_balance,
                'cold_address': ','.join(cold_wallet_addresses[wallet.blockchain]) if wallet.blockchain in cold_wallet_addresses else '',
                'total_balance': total_balance,
                'updated_at': wallet.updated_at }) 

    def sum_wallet_balance(self, hostname, blockchain, include_cold_balance=True):
        numeric_const_pattern = '-Total\sBalance:\s+((?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ )?)'
        rx = re.compile(numeric_const_pattern, re.VERBOSE)
        found_balance = False
        sum = 0
        for wallet in self.wallets:
            if wallet.hostname == hostname and wallet.blockchain == blockchain:
                try:
                    for balance in rx.findall(wallet.details):
                        #app.logger.info("Found balance of {0} for for {1} - {2}".format(balance, 
                        # wallet.hostname, wallet.blockchain))
                        sum += locale.atof(balance)
                        found_balance = True
                except Exception as ex:
                    app.logger.info("Failed to find current wallet balance number for {0} - {1}: {2}".format(
                        wallet.hostname, wallet.blockchain, str(ex)))
                if include_cold_balance and wallet.cold_balance:
                    sum += locale.atof(wallet.cold_balance)
        if found_balance:
            return converters.round_balance(sum)
        return '?'

class Keys:

    def __init__(self, keys):
        self.columns = ['hostname', 'details', 'updated_at']
        self.rows = []
        for key in keys:
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(key.hostname))
                displayname = w.get_worker(key.hostname, key.blockchain).displayname
            except:
                app.logger.info("Unable to find a worker with hostname '{0}'".format(key.hostname))
                displayname = key.hostname
            self.rows.append({ 
                'displayname': displayname, 
                'hostname': key.hostname,
                'blockchain': key.blockchain,
                'details': key.details,
                'updated_at': key.updated_at }) 

class Blockchains:

    def __init__(self, blockchains):
        self.columns = ['hostname', 'blockchain', 'details', 'updated_at']
        self.rows = []
        for blockchain in blockchains:
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(blockchain.hostname))
                displayname = w.get_worker(blockchain.hostname, blockchain.blockchain).displayname
            except:
                app.logger.info("Unable to find a worker with hostname '{0}'".format(blockchain.hostname))
                displayname = blockchain.hostname
            self.rows.append({ 
                'displayname': displayname, 
                'hostname': blockchain.hostname,
                'blockchain': blockchain.blockchain, 
                'details': blockchain.details,
                'updated_at': blockchain.updated_at }) 
            
class PartialsChartData:

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

    
class Connections:

    def __init__(self, connections):
        self.rows = []
        self.blockchains = {}
        for connection in connections:
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(connection.hostname))
                displayname = w.get_worker(connection.hostname, connection.blockchain).displayname
            except:
                app.logger.info("Unable to find a worker with hostname '{0}'".format(connection.hostname))
                displayname = connection.hostname
            self.rows.append({
                'displayname': displayname, 
                'hostname': connection.hostname,
                'blockchain': connection.blockchain,
                'farmer_port': self.blockchain_port(connection.blockchain),
                'details': connection.details,
                'add_exmample': self.get_add_connection_example(connection.blockchain)
            })
            self.blockchains[connection.blockchain] = self.parse(connection, connection.blockchain)
        self.rows.sort(key=lambda conn: conn['blockchain'])
    
    def get_add_connection_example(self, blockchain):
        if blockchain == 'cactus':
            return "101.127.109.238:11444"
        if blockchain == 'chia':
            return "node.chia.net:8444"
        if blockchain == 'chives':
            return "106.225.229.73:9699"
        if blockchain == 'cryptodoge':
            return "46.75.50.16:15994"
        if blockchain == 'flax':
            return "143.198.76.157:6888"
        if blockchain == 'flora':
            return "186.123.88.33:18644"
        if blockchain == 'hddcoin':
            return "145.1.235.18:28444"
        if blockchain == 'maize':
            return "212.159.183.209:8644"
        if blockchain == 'nchain':
            return "218.88.205.216:58445"
        if blockchain == 'staicoin':
            return "173.54.12.193:1999"
        if blockchain == 'stor':
            return "118.33.225.159:8668"
        
    def blockchain_port(self,blockchain):
        if blockchain == 'cactus':
            return 11444
        if blockchain == 'chia':
            return 8444
        if blockchain == 'chives':
            return 9699
        if blockchain == 'cryptodoge':
            return 15994
        if blockchain == 'flax':
            return 6888
        if blockchain == 'flora':
            return 18644
        if blockchain == 'hddcoin':
            return 28444
        if blockchain == 'nchain':
            return 58445
        if blockchain == 'maize':
            return 8644
        if blockchain == 'silicoin':
            return 22222
        if blockchain == 'staicoin':
            return 1999
        if blockchain == 'stor':
            return 8668

        raise("Unknown blockchain fork of selected: " + blockchain)

    def parse(self, connection, blockchain):
        conns = []
        for line in connection.details.split('\n'):
            try:
                if line.strip().startswith('Connections:'):
                    pass
                elif line.strip().startswith('Type'):
                    self.columns = line.lower().replace('last connect', 'last_connect') \
                        .replace('mib up|down', 'mib_up mib_down').strip().split()
                elif line.strip().startswith('-SB Height'):
                    groups = re.search("-SB Height:\s+(\d+)\s+-Hash:\s+(\w+)...", line.strip())
                    if not groups:
                        app.logger.info("Malformed SB Height line: {0}".format(line))
                    else:
                        height = groups[1]
                        hash = groups[2]
                        connection['height'] = height
                        connection['hash'] = hash
                        conns.append(connection)
                elif len(line.strip()) == 0:
                    pass
                else:
                    vals = line.strip().split()
                    if len(vals) > 7:
                        connection = {
                            'type': vals[0],
                            'ip': vals[1],
                            'ports': vals[2],
                            'nodeid': vals[3].replace('...',''),
                            'last_connect': datetime.datetime.strptime( \
                                str(datetime.datetime.today().year) + ' ' + vals[4] + ' ' + vals[5] + ' ' + vals[6], 
                                '%Y %b %d %H:%M:%S'),
                            'mib_up': float(vals[7].split('|')[0]),
                            'mib_down': float(vals[7].split('|')[1])
                        }
                        if len(vals) > 9: # HDDCoin keeps SBHeight and Hash on same line
                            connection['height'] = vals[8]
                            connection['hash'] = vals[9]
                        if blockchain == 'hddcoin' or vals[0] != "FULL_NODE":  # FARMER and WALLET only on one line 
                            conns.append(connection)
                    else:
                        app.logger.info("Bad connection line: {0}".format(line))
            except:
                app.logger.info(traceback.format_exc())
        return conns

class Plotnfts:

    def __init__(self, plotnfts):
        self.columns = ['hostname', 'details', 'updated_at']
        self.rows = []
        for plotnft in plotnfts:
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(plotnft.hostname))
                displayname = w.get_worker(plotnft.hostname).displayname
            except:
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