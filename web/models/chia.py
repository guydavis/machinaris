import datetime
import json
import locale
import os
import re
import time
import traceback

from common.config import globals

if "chia" == globals.enabled_blockchains()[0]:
    # https://github.com/Chia-Network/chia-blockchain/blob/main/chia/util/bech32m.py
    from chia.util import bech32m

from flask_babel import _, lazy_gettext as _l, format_decimal

from web import app
from web.actions import worker as w, mapping
from common.config import globals
from common.utils import converters, fiat

# Treat *.plot files smaller than this as in-transit (copying) so don't count them
MINIMUM_K32_PLOT_SIZE_BYTES = 100 * 1024 * 1024

BLOCKCHAIN_STATUSES_CACHE_FILE = '/root/.chia/machinaris/cache/blockchain_statuses_cache.json'

class Summaries:

    def __init__(self, blockchains, farms, wallets, stats):
        self.rows = []
        for blockchain in blockchains.rows:
            app.logger.debug("Adding summary row for {0}".format(blockchain['blockchain']))
            farm = self.find_farm(farms, blockchain['blockchain'])
            if not farm:
                app.logger.error("No farm summary found for {0}".format(blockchain['blockchain']))
                continue
            blockhain_for_wallet = blockchain['blockchain']
            wallet = self.find_wallet(wallets, blockhain_for_wallet)
            if not wallet:
                app.logger.error("No wallet found for {0}".format(blockhain_for_wallet))
                continue
            if not blockchain['blockchain'] in stats:
                app.logger.error("No blockhain stats for {0} in {1}".format(blockchain['blockchain'], stats.keys()))
                continue
            blockchain_stats = stats[blockchain['blockchain']]
            # Now collect each value in a separate try/except to guard against missing data
            try:
                status = blockchain['status']
            except:
                status = ''
                app.logger.error("No status found for blockchain: {0}".format(blockchain))
            try:
                farmed = farm['total_coins']
            except:
                farmed = ''
                app.logger.error("No total_coins found for farm: {0}".format(farm))
            try:
                wallet_balance_float = wallet['total_balance_float']
                wallet_balance = wallet['total_balance']
            except:
                wallet_balance_float = 0
                wallet_balance = ''
                app.logger.error("No total_balance found for wallet: {0}".format(wallet))
            try:
                height = blockchain['peak_height']
            except:
                height = ''
                app.logger.error("No peak_height found for blockchain: {0}".format(blockchain))
            try:
                height = blockchain['peak_height']
            except:
                height = ''
                app.logger.error("No peak_height found for blockchain: {0}".format(blockchain))
            try:
                plots = farm['plot_count']
            except:
                plots = ''
                app.logger.error("No plot_count found for farm: {0}".format(farm))
            try:
                etw = self.etw_to_days(blockchain['blockchain'], farm['expected_time_to_win_english'])
            except:
                etw = ''
                app.logger.error("No expected_time_to_win found for farm: {0}".format(farm))
            try:
                harvesters = blockchain_stats['harvesters']
            except:
                harvesters = ''
                app.logger.error("No harvesters found for blockchain stats: {0}".format(blockchain_stats))
            try:
                max_resp = blockchain_stats['max_resp']
            except:
                max_resp = ''
                app.logger.error("No max_resp found for blockchain stats: {0}".format(blockchain_stats))
            try:
                partials_per_hour = blockchain_stats['partials_per_hour']
            except:
                partials_per_hour = ''
                app.logger.error("No partials_per_hour found for blockchain stats: {0}".format(blockchain_stats))
            try:
                edv = blockchain_stats['edv']
            except:
                edv = ''
                app.logger.error("No edv found for blockchain stats: {0}".format(blockchain_stats))
            try:
                edv_fiat = blockchain_stats['edv_fiat']
            except:
                edv_fiat = ''
                app.logger.error("No edv_fiat found for blockchain stats: {0}".format(blockchain_stats))
            try:
                effort = blockchain_stats['effort']
            except:
                effort = ''
                app.logger.error("No effort found for blockchain stats: {0}".format(blockchain_stats))
            self.rows.append({
                'blockchain': blockchain['blockchain'],
                'status': status,
                'farmed': farmed,
                'wallet': wallet_balance,
                'fiat': fiat.to_fiat(blockchain['blockchain'], wallet_balance_float),
                'height': height,
                'plots': plots,
                'harvesters': harvesters, 
                'max_resp': max_resp, 
                'partials_per_hour': partials_per_hour,
                'edv': edv, 
                'edv_fiat': edv_fiat,
                'effort': effort, 
                'etw': etw,
            })

    def find_farm(self, farms, blockchain):
        if blockchain in farms:
            return farms[blockchain]

    def find_wallet(self, wallets, blockchain):
        for wallet in wallets.rows:
            if wallet['blockchain'] == blockchain:
                return wallet

    def etw_to_days(self, blockchain, etw):
        #app.logger.info("{0} -> {1}".format(blockchain, etw))
        try:
            minutes = converters.etw_to_minutes(etw)
            #app.logger.info("Converting {0} minutes.".format(minutes))
            days = minutes/60/24
            if days > 10:
                days = round(days)
            elif days > 1:
                days = round(days, 1)
            else:
                days = round(days, 2)
            return "{0} {1}".format(format_decimal(days), _('days'))
        except Exception as ex:
            app.logger.info("Unable to convert ETW to minutes '{0}' because {1}.".format(etw, str(ex)))
            return etw

class FarmSummary:

    def __init__(self, farm_recs, wallet_recs):
        self.farms = {}
        self.wallets = Wallets(wallet_recs)
        for farm_rec in farm_recs: 
            if "fullnode" in farm_rec.mode:
                try:
                    app.logger.debug("Searching for worker with hostname '{0}'".format(farm_rec.hostname))
                    wkr = w.get_worker(farm_rec.hostname, farm_rec.blockchain)
                    if wkr:
                        displayname = wkr.displayname
                        connection_status = wkr.connection_status()
                    else:
                        app.logger.info("Unable to find a worker with hostname '{0}' and blockchain '{1}'".format(farm_rec.hostname, farm_rec.blockchain))
                        displayname = farm_rec.hostname
                        connection_status = None
                except Exception as ex:
                    app.logger.info("FarmSummary.init(): Error finding a worker with hostname '{0}' and blockchain '{1}'".format(farm_rec.hostname, farm_rec.blockchain))
                    displayname = farm_rec.hostname
                    connection_status = None
                try:
                    if farm_rec.blockchain == 'mmx':
                        wallet_balance = self.wallets.sum_mmx_wallet_balance(farm_rec.hostname, farm_rec.blockchain)
                    else:
                        wallet_balance = self.wallets.sum_chia_wallet_balance(farm_rec.hostname, farm_rec.blockchain)
                except: 
                    wallet_balance = '?'
                if farm_rec.total_coins:
                    total_coins = converters.round_balance(farm_rec.total_coins)
                else:
                    total_coins = converters.round_balance(0)
                try:
                    plots_display_size = converters.gib_to_fmt(farm_rec.plots_size)
                except:
                    plots_display_size = ''
                try:
                    netspace_display_size = converters.gib_to_fmt(farm_rec.netspace_size)
                except:
                    netspace_display_size = '?'
                try:
                    blockchain_symbol = globals.get_blockchain_symbol(farm_rec.blockchain)
                except:
                    blockchain_symbol = None
                farm = {
                    "plot_count": int(farm_rec.plot_count),
                    "plots_size": farm_rec.plots_size,
                    "plots_display_size": plots_display_size,
                    "status": farm_rec.status,
                    "display_status": self.status_if_responding(displayname, farm_rec.blockchain, connection_status, farm_rec.status),
                    "total_coins": total_coins,
                    "wallet_balance": converters.round_balance(wallet_balance),
                    "currency_symbol": blockchain_symbol,
                    "netspace_display_size": netspace_display_size,
                    "netspace_size": farm_rec.netspace_size,
                    "expected_time_to_win": self.i18n_etw(farm_rec.expected_time_to_win),
                    "expected_time_to_win_english": farm_rec.expected_time_to_win,
                }
                if not farm_rec.blockchain in self.farms:
                    self.farms[farm_rec.blockchain] = farm
                else:
                    app.logger.info("Discarding duplicate fullnode blockchain status from {0} - {1}".format(farm_rec.hostname, farm_rec.blockchain))    
            else:
                app.logger.info("Stale farm status for {0} - {1}".format(farm_rec.hostname, farm_rec.blockchain))
        if len(self.farms) == 0:  # Handle completely missing farm summary info 
            self.farms['chia'] = {} # with empty chia farm
        #app.logger.info(self.farms.keys())

    def status_if_responding(self, displayname, blockchain, connection_status, last_status):
        app.logger.debug("Blockchain {0} status is {1}".format(blockchain, last_status))
        if connection_status == 'Responding':
            if last_status == "Farming":
                return _("Active")
            if last_status == "Syncing":
                return _("Syncing")
            if last_status == "Not available":
                return _("Not available")
            if last_status == "Not synced or not connected to peers":
                return _("Not synced")
            return last_status
        #app.logger.info("Oops! {0} ({1}) had connection_success: {2}".format(displayname, blockchain, connection_status))
        return _("Offline")

    def selected_blockchain(self):
        blockchains = list(self.farms.keys())
        blockchains.sort()
        for blockchain in blockchains:
            if blockchain == globals.enabled_blockchains()[0]:
                return blockchain
        return blockchains[0]

    # This is intentionally verbose to allow Babel to extract each english date unit
    def i18n_etw(self, etw):
        if 'years' in etw:
            etw = etw.replace('years', _('years'))
        if 'year' in etw:
            etw = etw.replace('year', _('year'))
        if 'months' in etw:
            etw = etw.replace('months', _('months'))
        if 'month' in etw:
            etw = etw.replace('month', _('month'))
        if 'weeks' in etw:
            etw = etw.replace('weeks', _('weeks'))
        if 'week' in etw:
            etw = etw.replace('week', _('week'))
        if 'days' in etw:
            etw = etw.replace('days', _('days'))
        if 'day' in etw:
            etw = etw.replace('day', _('day'))
        if 'hours' in etw:
            etw = etw.replace('hours', _('hours'))
        if 'hour' in etw:
            etw = etw.replace('hour', _('hour'))
        if 'minutes' in etw:
            etw = etw.replace('minutes', _('minutes'))
        if 'minute' in etw:
            etw = etw.replace('minute', _('minute'))
        if 'never (no plots)' in etw.lower():
            etw = etw.replace('Never (no plots)', _('Never (no plots)'))
        if 'soon' in etw.lower():
            etw = etw.replace('Soon', _('Soon'))
        if 'and' in etw:
            etw = etw.replace('and', _('and'))
        return etw

class FarmPlots:

    def __init__(self, plots):
        self.columns = [ 
            _('worker'), 
            _('blockchain'), 
            _('plot_id'),  
            _('dir'),
            _('plot'), 
            _('type'), 
            _('create_date'), 
            _('size'), 
            _('c'), 
            _('a')
        ]
        self.rows = []
        for plot in plots:
            self.rows.append([
                plot.displayname,  
                plot.blockchain, 
                plot.plot_id, 
                plot.dir,  
                #app.jinja_env.filters['plotnameshortener'](plot.file),
                plot.file,
                plot.type if plot.type else "", 
                plot.created_at, 
                app.jinja_env.filters['bytesfilter'](plot.size),
                self.get_check_cell_value(plot.plot_id, plot.plot_check),
                self.get_analzye_cell_value(plot.plot_id, plot.plot_analyze),
            ])

    def get_analzye_cell_value(self, plot_id, plot_analyze):
        if plot_analyze and plot_analyze != '-':
            if '|' in plot_analyze:
                analyze_seconds = plot_analyze.split('|')[1]
            else: # Old format, just seconds
                analyze_seconds =  plot_analyze
            return "{0} | {1}".format(analyze_seconds, plot_id)
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
            app.logger.debug("Wallets.init(): Parsing wallet for blockchain: {0}".format(wallet.blockchain))
            worker_status = None
            service_status = None
            try:
                app.logger.debug("Wallets.init(): Found worker with hostname '{0}'".format(wallet.hostname))
                worker = w.get_worker(wallet.hostname, wallet.blockchain)
                worker_status = worker.connection_status()
                displayname = worker.displayname
                try:
                    service_status = json.loads(worker.config)['wallet_status']
                    app.logger.debug("For {0} found wallet service status: {1}".format(wallet.blockchain, service_status))
                except:
                    pass
            except:
                app.logger.info("Wallets.init(): Unable to find a worker with hostname '{0}'".format(wallet.hostname))
                displayname = wallet.hostname
            if wallet.blockchain == 'mmx':
                hot_balance = self.sum_mmx_wallet_balance(wallet.hostname, wallet.blockchain, False)
            else:
                hot_balance = self.sum_chia_wallet_balance(wallet.hostname, wallet.blockchain, False)
            try:
                cold_balance = converters.round_balance(float(wallet.cold_balance))
            except Exception as ex:
                app.logger.error("Failed to convert wallet.cold_balance {0} of type {1}".format(wallet.cold_balance, type(wallet.cold_balance), str(ex)))
                cold_balance = ''
            try:
                total_balance = float(hot_balance) + float(wallet.cold_balance)
            except Exception as ex:
                app.logger.error("Either failed to convert hot_balance  {0} of type {1}".format(hot_balance, type(hot_balance), str(ex)))
                app.logger.error("OR failed     to convert wallet.cold_balance {0} of type {1}".format(wallet.cold_balance, type(wallet.cold_balance), str(ex)))
                total_balance = hot_balance
            try:
                blockchain_symbol = globals.get_blockchain_symbol(wallet.blockchain).lower()
            except:
                blockchain_symbol = None
            self.rows.append({ 
                'displayname': displayname, 
                'hostname': wallet.hostname,
                'blockchain': wallet.blockchain,
                'status': self.extract_status(wallet.blockchain, wallet.details, wallet.updated_at, worker_status),
                'service': service_status,
                'details': self.link_to_wallet_transactions(wallet.blockchain, wallet.details),
                'hot_balance': converters.round_balance(hot_balance),
                'cold_balance': cold_balance,
                'cold_address': ','.join(cold_wallet_addresses[wallet.blockchain]) if wallet.blockchain in cold_wallet_addresses else '',
                'total_balance_float': total_balance,
                'total_balance': converters.round_balance(total_balance),
                'blockchain_symbol': blockchain_symbol,
                'fiat_balance': fiat.to_fiat(wallet.blockchain, total_balance),
                'updated_at': wallet.updated_at }) 

    def exclude_wallets_from_sum(self, wallet_details):
        details = []
        chunks = wallet_details.split('\n\n')
        for chunk in chunks:
            exclude_wallet = False
            lines = chunk.split('\n')
            for line in lines:
                if re.match('^\s+-Type:\s+CAT$', line) or re.match('^\s+-Type:\s+DISTRIBUTED_ID$', line) or re.match('^\s+-Type:\s+DECENTRALIZED_ID$', line) or re.match('^\s+-Type:\s+NFT$', line):
                    exclude_wallet = True
            if exclude_wallet:
                app.logger.debug("Ignoring balance of wallet named: {0}".format(lines[0][:-1]))
            else:
                details.extend(chunk.split('\n'))
        return '\n'.join(details)
    
    def extract_wallet_id(self, lines):
        for line in lines:
            wallet_match = re.match("^\s+-Wallet ID:\s+(\d)+$", line)
            if wallet_match:
                return wallet_match.group(1)
        return None

    def link_to_wallet_transactions(self, blockchain, details):
        lines = []
        if globals.legacy_blockchain(blockchain) or blockchain in ['cryptodoge']: 
            for line in details.split('\n'):
                if 'wallet id' in line.lower():
                    lines.append("<a href='#' class='text-white' title='" + _('View Transactions') + "' onclick='ViewTransactions(\""+ blockchain + "\", \"1\");return false;'>" + line.strip() + "</a>:")
                else:
                    lines.append(line)
        else: # Chia and updated blockchains, have multiple wallet id #s like 1,3,4 etc.
            details_lines = details.split('\n')
            for i in range(len(details_lines)):
                line = details_lines[i]
                if line.strip().endswith(':') and not line.strip() == 'Connections:':
                    wallet_name = line.strip()[:-1]
                    wallet_id = self.extract_wallet_id(details_lines[i+1:])
                    if wallet_name and wallet_id:
                        line = "<a href='#' class='text-white' title='" + _('View Transactions') + "' onclick='ViewTransactions(\""+ blockchain + "\", \"" + str(wallet_id) + "\");return false;'>" + wallet_name + "</a>:"
                lines.append(line)
                i += 1
        return '\n'.join(lines)

    def sum_chia_wallet_balance(self, hostname, blockchain, include_cold_balance=True):
        numeric_const_pattern = '-Total\sBalance:\s+((?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ )?)'
        rx = re.compile(numeric_const_pattern, re.VERBOSE)
        sum = 0
        for wallet in self.wallets:
            if wallet.hostname == hostname and wallet.blockchain == blockchain:
                try:
                    for balance in rx.findall(self.exclude_wallets_from_sum(wallet.details)):
                        #app.logger.info("Found balance of {0} for  {1} - {2}".format(balance, wallet.hostname, wallet.blockchain))
                        sum += locale.atof(balance)
                except Exception as ex:
                    app.logger.info("Failed to find current wallet balance number for {0} - {1}: {2}".format(
                        wallet.hostname, wallet.blockchain, str(ex)))
                if include_cold_balance and wallet.cold_balance:
                    sum += locale.atof(wallet.cold_balance)
        return sum

    def sum_mmx_wallet_balance(self, hostname, blockchain, include_cold_balance=True):
        numeric_const_pattern = 'Balance:\s+((?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ )?)\sMMX'
        rx = re.compile(numeric_const_pattern, re.VERBOSE)
        sum = 0
        for wallet in self.wallets:
            if wallet.hostname == hostname and wallet.blockchain == blockchain:
                try:
                    #app.logger.info(wallet.details)
                    for balance in rx.findall(wallet.details):
                        #app.logger.info("Found balance of {0} for {1} - {2}".format(balance, wallet.hostname, wallet.blockchain))
                        sum += locale.atof(balance)
                except Exception as ex:
                    app.logger.info("Failed to find current wallet balance number for {0} - {1}: {2}".format(
                        wallet.hostname, wallet.blockchain, str(ex)))
                if include_cold_balance and wallet.cold_balance:
                    sum += locale.atof(wallet.cold_balance)
        return sum

    def extract_status(self, blockchain, details, updated_at, worker_status):
        if worker_status == 'Responding':
            if not details:
                return None
            if updated_at and updated_at <= (datetime.datetime.now() - datetime.timedelta(minutes=5)):
                return "Paused"
            if blockchain == 'mmx':
                pattern = '^Synced:\s+(.*)$'
            else:
                pattern = '^Sync status: (.*)$'
            for line in details.split('\n'):
                m = re.match(pattern, line)
                if m:
                    status = m.group(1).strip()
                    if 'Yes' == status: # MMX
                        return "Synced"
                    if 'No' == status: # MMX
                        return "Syncing" 
                    return status
        return "Offline"

class Keys:

    def __init__(self, keys):
        self.columns = ['hostname', 'details', 'updated_at']
        self.rows = []
        for key in keys:
            worker_status = None
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(key.hostname))
                worker = w.get_worker(key.hostname, key.blockchain)
                worker_status = worker.connection_status()
                displayname = worker.displayname
            except:
                app.logger.info("Keys.init(): Unable to find a worker with hostname '{0}'".format(key.hostname))
                displayname = key.hostname
            parsed_details = key.details
            try:
                [addresses, parsed_details] = self.link_first_wallet_address(key.blockchain, key.details)
            except:
                traceback.print_exc()
                parsed_details = key.details
                addresses = []
            self.rows.append({ 
                'displayname': displayname, 
                'hostname': key.hostname,
                'blockchain': key.blockchain,
                'status': worker_status,
                'details': parsed_details,
                'addresses': addresses,
                'updated_at': key.updated_at }) 
    
    def link_first_wallet_address(self, blockchain, details):
        addresses = []
        alltheblocks_blockchain = globals.get_alltheblocks_name(blockchain)
        lines = []
        for line in details.split('\n'):
            if line.startswith('First wallet address'):
                label = line.split(':')[0]
                address = line.split(':')[1].strip()
                addresses.append(address)
                link = "https://alltheblocks.net/{0}/address/{1}".format(alltheblocks_blockchain, address)
                lines.append("{0}: <a target='_blank' class='text-white' href='{1}'>{2}</a>".format(label, link, address))
            else:
                lines.append(line)
        return [addresses, '\n'.join(lines)]

class Blockchains:

    def __init__(self, blockchains):
        self.columns = ['hostname', 'blockchain', 'details', 'updated_at']
        self.rows = []
        atb_statuses = self.load_atb_blockchain_statuses()
        for blockchain in blockchains:
            worker_status = None
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(blockchain.hostname))
                worker = w.get_worker(blockchain.hostname, blockchain.blockchain)
                worker_status = worker.connection_status()
                displayname = worker.displayname
            except:
                app.logger.info("Blockchains.init(): Unable to find a worker with hostname '{0}'".format(blockchain.hostname))
                displayname = blockchain.hostname
            row = { 
                'displayname': displayname, 
                'hostname': blockchain.hostname,
                'blockchain': blockchain.blockchain, 
                'status': self.extract_status(blockchain.blockchain, blockchain.details, worker_status),
                'peak_height': self.extract_height(blockchain.blockchain, blockchain.details),
                'peak_time': self.extract_time(blockchain.blockchain, blockchain.details),
                'fiat_price': fiat.to_fiat(blockchain.blockchain, 1.0),
                'fiat_price_tooltip': fiat.tooltip(blockchain.blockchain),
                'details': blockchain.details,
                'updated_at': blockchain.updated_at 
            }
            try:
                if blockchain.blockchain in atb_statuses:
                    if 'sync_state' in atb_statuses[blockchain.blockchain]:
                        row['atb_sync_status'] = atb_statuses[blockchain.blockchain]['sync_state']
                    if 'peak_height' in atb_statuses[blockchain.blockchain]:
                        row['atb_peak_height'] = atb_statuses[blockchain.blockchain]['peak_height']
                    if 'peak_time' in atb_statuses[blockchain.blockchain]:
                        row['atb_peak_time'] = atb_statuses[blockchain.blockchain]['peak_time']
                elif blockchain.blockchain != 'mmx':
                    app.logger.info("No ATB blockchain status found for: {0}".format(blockchain.blockchain))
            except Exception as ex:
                app.logger.info("Failed to include ATB blockchain status because {0}".format(str(ex)))
            self.rows.append(row) 
    
    def load_atb_blockchain_statuses(self):
        data = {}
        if os.path.exists(BLOCKCHAIN_STATUSES_CACHE_FILE):
            try:
                with open(BLOCKCHAIN_STATUSES_CACHE_FILE) as f:
                    data = json.load(f)
            except Exception as ex:
                msg = "Unable to read ATB blockchain status cache from {0} because {1}".format(BLOCKCHAIN_STATUSES_CACHE_FILE, str(ex))
                print(msg)
        if 'chia' in data:
            data['gigahorse'] = data['chia'] # Same status for both
        return data
    
    def extract_status(self, blockchain, details, worker_status):
        if worker_status == 'Responding':
            if not details:
                return None
            if blockchain == 'mmx':
                pattern = '^Synced: (.*)$'
            elif blockchain == 'staicoin': # Staicoin being different for no good reason...
                pattern = '^Current Node Status: (.*)$'
            else:
                pattern = '^Current Blockchain Status: (.*)$'
            for line in details.split('\n'):
                m = re.match(pattern, line)
                if m: 
                    status = m.group(1).strip()
                    if status == "Full Node Synced":
                        return "Synced"
                    if 'Syncing' in status:
                        return "Syncing"
                    if 'Not Synced' in status:
                        return 'Not Synced'
                    if 'Yes' == status: # MMX
                        return "Synced"
                    if 'No' == status: # MMX
                        return "Syncing" 
                    if 'Peer(s) Stalled' in status: # Staicoin
                        return "Peer(s) Stalled"
                    return status
            return "Error"
        return "Offline"

    def extract_height(self, blockchain, details):
        if not details:
            return None
        if blockchain == 'mmx':
            pattern = '^Height:\s+(\d+)$'
        else:
            pattern = '^.* Height:\s+(\d+)$'
        for line in details.split('\n'):
            m = re.match(pattern, line)
            if m: 
                return m.group(1).strip()
        return None

    def extract_time(self, blockchain, details):
        if not details:
            return None
        if blockchain == 'mmx':
            return '-' # None for MMX
        pattern = '^\s+Time:\s+(.*)\sHeight:.*$'
        for line in details.split('\n'):
            m = re.match(pattern, line)
            if m:
                try:
                    peak_time = datetime.datetime.strptime(m.group(1).strip(), '%a %b %d %Y %H:%M:%S %Z')
                    return peak_time.strftime("%Y-%m-%d %H:%M")
                except:
                    return m.group(1).strip() # Unconverted time
        return None

class Connections:

    def __init__(self, connections, lang):
        self.rows = []
        self.blockchains = {}
        geoip_cache = mapping.load_geoip_cache()
        for connection in connections:
            worker_status = None
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(connection.hostname))
                worker = w.get_worker(connection.hostname, connection.blockchain)
                worker_status = worker.connection_status()
                displayname = worker.displayname
            except:
                app.logger.info("Connections.init(): Unable to find a worker with hostname '{0}'".format(connection.hostname))
                displayname = connection.hostname
            try:
                farmer_port = globals.get_blockchain_network_port(connection.blockchain)
            except:
                farmer_port = None
            self.rows.append({
                'displayname': displayname, 
                'hostname': connection.hostname,
                'blockchain': connection.blockchain,
                'status': worker_status,
                'farmer_port': farmer_port,
                'details': connection.details
            })
            if connection.blockchain == 'mmx':
                self.blockchains[connection.blockchain] = self.parse_mmx(connection, connection.blockchain, geoip_cache, lang)
            else:
                self.blockchains[connection.blockchain] = self.parse_chia(connection, connection.blockchain, geoip_cache, lang)
        self.rows.sort(key=lambda conn: conn['blockchain'])
    
    def get_geoname_for_lang(self, ip, location, lang):
        lang_codes = [ lang, ]
        if '_' in lang: 
            lang_codes.append(lang.split('_')[0]) # Secondarily, add more generic code
        for lang_code in lang_codes:
            for key in location:
                if key.startswith(lang_code): # Note, means a pt_PT user may get pt_BR as that's the only 'pt' that Maxmind provides
                    #app.logger.info('Found matching geoname for {0} in {1}'.format(lang, location))
                    return location[key]
        if 'en' in location: # Default fallback is 'en'
            app.logger.info('Falling back to English geoname at {0} for {1} in {2}'.format(ip, lang, location))
            return location['en']
        app.logger.debug('Unable to find a geoname at {0} for {1} in {2}'.format(ip, lang, location))
        return '' # Blank if no such match

    def set_geolocation(self, geoip_cache, connection, lang):
        latitude = None
        longitude = None
        city = ''
        country = ''
        if connection['ip'] in geoip_cache and geoip_cache[connection['ip']]:
            geoip = geoip_cache[connection['ip']]
            latitude = geoip['latitude']
            longitude = geoip['longitude']
            try:
                city = self.get_geoname_for_lang(connection['ip'], geoip['city'], lang)
            except:
                traceback.print_exc()
            try:
                country = self.get_geoname_for_lang(connection['ip'], geoip['country'], lang)
            except:
                traceback.print_exc()
        connection['latitude'] = latitude
        connection['longitude'] = longitude
        connection['city'] = city
        connection['country'] = country

    def parse_chia(self, connection, blockchain, geoip_cache, lang):
        conns = []
        for line in connection.details.split('\n'):
            try:
                if line.strip().startswith('Connections:') or \
                    line.strip().startswith('Connection error.') or \
                    line.strip().startswith('This is normal if full node'):
                    pass
                elif line.strip().startswith('Type'):
                    self.columns = line.lower().replace('last connect', 'last_connect') \
                        .replace('mib up|down', 'mib_up mib_down').strip().split()
                elif line.strip().startswith('-SB Height') or line.strip().startswith('-Height'):
                    groups = re.search("Height:\s+(\d+)\s+-Hash:\s+(\w+)...", line.strip())
                    if not groups:
                        app.logger.info("Malformed Height line: {0}".format(line))
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
                        last_connect = str(datetime.datetime.today().year) + ' ' + vals[4] + ' ' + vals[5] + ' ' + vals[6]
                        connection = {
                            'type': vals[0],
                            'ip': vals[1],
                            'ports': vals[2],
                            'nodeid': vals[3].replace('...',''),
                            'last_connect': datetime.datetime.strptime(last_connect, '%Y %b %d %H:%M:%S'),
                            'mib_up': float(vals[7].split('|')[0]),
                            'mib_down': float(vals[7].split('|')[1])
                        }
                        if len(vals) > 9 and vals[8] != '-Trusted:': # HDDCoin keeps SBHeight and Hash on same line
                            connection['height'] = vals[8]
                            connection['hash'] = vals[9]
                        try:
                            self.set_geolocation(geoip_cache, connection, lang)
                        except:
                            traceback.print_exc()
                        if blockchain == 'hddcoin' or vals[0] != "FULL_NODE":  # FARMER and WALLET only on one line 
                            conns.append(connection)
                    else:
                        app.logger.info("Bad connection line: {0}".format(line))
            except:
                app.logger.info("Exception parsing connection line: {0}".format(line))
                app.logger.info(traceback.format_exc())
        return conns

    def parse_mmx(self, connection, blockchain, geoip_cache, lang):
        conns = []
        for line in connection.details.split('\n'):
            try:
                #app.logger.info(line)
                m = re.match("\[(.+)\]\s+height\s+=\s+(\!?\d+), (\w+) \(\d+\.\d+\), (\d+\.?\d*) (\w)B recv, (\d*\.?\d*) (\w)B sent,.* since (\d+) min, .* (\d+\.?\d?) sec timeout", line.strip(), re.IGNORECASE)
                if m:
                    connection = {
                        'type': m.group(3),
                        'ip': m.group(1),
                        'height': m.group(2),
                        'ports': '',
                        'nodeid': '',
                        'last_connect': 'since {0} min'.format(m.group(8)),
                        'mib_up': "%.1f"% round(self.rate_to_mb(m.group(6), m.group(7)) * int(m.group(8)) * 60, 2),
                        'mib_down': "%.1f"% round(self.rate_to_mb(m.group(4), m.group(5)) * int(m.group(8)) * 60, 2),
                        'timeout': m.group(9)
                    }
                    try:
                        self.set_geolocation(geoip_cache, connection, lang)
                    except:
                        traceback.print_exc()
                    conns.append(connection)
                elif line.strip():
                    app.logger.info("Bad peer line: {0}".format(line))
            except:
                app.logger.info(traceback.format_exc())
        return conns

    def rate_to_mb(self, rate, unit):
        if unit.lower() == 'k':
            try:
                return float(rate) / 1024
            except:
                app.logger.error("Invalid transmission rate in KB/sec provided: {0}".format(rate))
                return rate
        elif unit.lower() == 'm':
            return float(rate)
        else:
            app.logger.error("Unknown transmission rate unit character of {0} encountered.".format(unit))
            return rate

class Transactions:

    def __init__(self, blockchain, transactions):
        try:
            self.address_prefix = globals.get_blockchain_symbol(blockchain).lower()
        except:
            self.address_prefix = None
        self.transactions = transactions
        self.rows = []
        for t in transactions:
            to_puzzle_hash = t['to_puzzle_hash'][2:]  # Strip off leading 0x from hex string
            self.rows.append({
                "type": self.lookup_type(t['type']),
                "to": bech32m.encode_puzzle_hash(bytes.fromhex(to_puzzle_hash), self.address_prefix),
                "status": _('Confirmed') if 'confirmed_at_height' in t else '',
                "amount": converters.round_balance(self.mojos_to_coin(blockchain, t['amount'])),
                "fee": t['fee_amount'],
                "created_at": time.strftime('%Y-%m-%d %H:%M', time.localtime(t['created_at_time'])),
            })

    def mojos_to_coin(self, blockchain, mojos):
        return mojos / globals.get_mojos_per_coin(blockchain)
    
    # https://github.com/Chia-Network/chia-blockchain/blob/main/chia/wallet/util/transaction_type.py
    def lookup_type(self, type_id):
        if type_id == 0:
            return _('INCOMING_TX')
        if type_id == 1:
            return _('OUTGOING_TX')
        if type_id == 2:
            return _('COINBASE_REWARD')
        if type_id == 3:
            return _('FEE_REWARD')
        if type_id == 4:
            return _('INCOMING_TRADE')
        if type_id == 5:
            return _('OUTGOING_TRADE')
