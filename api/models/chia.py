import locale
import os
import re
import traceback

from datetime import datetime

from api import app, utils
from common.config import globals
from common.utils import converters, fiat
from common.models import wallets as w

class FarmSummary:

    def __init__(self, cli_stdout, blockchain):
            self.plot_count = 0
            self.plots_size = 0
            for line in cli_stdout:
                if "Plot count for all" in line: 
                    self.plot_count = line.strip().split(':')[1].strip()
                elif "Total size of plots" in line:
                    self.plots_size = line.strip().split(':')[1].strip()
                elif "status" in line: 
                    self.calc_status(line.split(':')[1].strip())
                elif re.match("Total.*farmed:.*$", line):
                    self.total_coins = line.split(':')[1].strip()
                elif "network space" in line:
                    self.calc_netspace_size(line.split(':')[1].strip())
                elif "Expected time to win" in line:
                    self.time_to_win = line.split(':')[1].strip()
                elif "User transaction fees" in line:
                    self.transaction_fees = line.split(':')[1].strip()

    def calc_status(self, status):
        self.status = status
        if self.status == "Farming":
            self.display_status = "Active"
        else:
            self.display_status = self.status

    def calc_netspace_size(self, netspace_size):
        self.netspace_size = netspace_size
        try:
            size_value, size_unit = netspace_size.split(' ')
            if float(size_value) > 1000 and size_unit == 'PiB':
                self.display_netspace_size = "{:0.3f} EiB".format(float(size_value) / 1000)
            else:
                self.display_netspace_size = self.netspace_size
        except:
            app.logger.debug("Unable to split network size value: {0}".format(netspace_size))
            self.display_netspace_size = self.netspace_size

class HarvesterSummary:

    def __init__(self):
        self.status = "Harvesting" # TODO Check for harvester status in debug.log

class Wallet:

    def __init__(self, cli_stdout):
        self.text = ""
        lines = cli_stdout.split('\n')
        for line in lines:
            app.logger.info("WALLET LINE: {0}".format(line))
            if "No online" in line or \
                "skip restore from backup" in line or \
                "own backup file" in line or \
                "SIGWINCH" in line or \
                "data_layer.crt" in line:
                continue
            self.text += line + '\n'

class Wallets:

    def __init__(self, wallets, cold_wallet_addresses={}):
        self.wallets = wallets
        self.columns = ['hostname', 'details', 'updated_at']
        self.rows = []
        self.cold_wallet_addresses = cold_wallet_addresses
        for wallet in wallets:
            app.logger.debug("Wallets.init(): Parsing wallet for blockchain: {0}".format(wallet.blockchain))
            if wallet.blockchain == 'mmx':
                hot_balance = self.sum_mmx_wallet_balance(wallet.hostname, wallet.blockchain, False)
            else:
                hot_balance = self.sum_chia_wallet_balance(wallet.hostname, wallet.blockchain, False)
            try:
                cold_balance = float(wallet.cold_balance)
            except:
                cold_balance = 0.0
            try:
                total_balance = float(hot_balance) + float(cold_balance)
            except:
                total_balance = hot_balance
            if hot_balance:
                self.rows.append({ 
                    'hostname': wallet.hostname,
                    'blockchain': wallet.blockchain,
                    'total_balance': total_balance,
                    'cold_balance': wallet.cold_balance,
                    'fiat_balance': fiat.to_fiat_float(wallet.blockchain, total_balance),
                    'updated_at': wallet.updated_at })
            else:
                app.logger.debug("api.models.Wallets.init(): Skipping blockchain {0}".format(wallet.blockchain))

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

    def sum_chia_wallet_balance(self, hostname, blockchain, include_cold_balance=True):
        numeric_const_pattern = '-Total\sBalance:\s+((?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ )?)'
        rx = re.compile(numeric_const_pattern, re.VERBOSE)
        sum = 0
        for wallet in self.wallets:
            if wallet.hostname == hostname and wallet.blockchain == blockchain and wallet.is_synced():
                try:
                    for balance in rx.findall(self.exclude_wallets_from_sum(wallet.details)):
                        #app.logger.info("Found balance of {0} for for {1} - {2}".format(balance, 
                        # wallet.hostname, wallet.blockchain))
                        sum += locale.atof(balance)
                        found_balance = True
                except Exception as ex:
                    app.logger.info("Failed to find current wallet balance number for {0} - {1}: {2}".format(
                        wallet.hostname, wallet.blockchain, str(ex)))
                if include_cold_balance and wallet.cold_balance:
                    sum += locale.atof(wallet.cold_balance)
        return sum

    def sum_mmx_wallet_balance(self, hostname, blockchain, include_cold_balance=True):
        numeric_const_pattern = 'Balance:\s+((?: (?: \d*\.\d+ ) | (?: \d+\.? ) )(?: [Ee] [+-]? \d+ )?)'
        rx = re.compile(numeric_const_pattern, re.VERBOSE)
        sum = 0
        for wallet in self.wallets:
            if wallet.hostname == hostname and wallet.blockchain == blockchain:
                try:
                    #app.logger.info(wallet.details)
                    for balance in rx.findall(wallet.details):
                        #app.logger.info("Found balance of {0} for for {1} - {2}".format(balance, wallet.hostname, wallet.blockchain))
                        sum += locale.atof(balance)
                        found_balance = True
                except Exception as ex:
                    app.logger.info("Failed to find current wallet balance number for {0} - {1}: {2}".format(
                        wallet.hostname, wallet.blockchain, str(ex)))
                if include_cold_balance and wallet.cold_balance:
                    sum += locale.atof(wallet.cold_balance)
        return sum

class Keys:

    def __init__(self, cli_stdout):
        self.text = ""
        for line in cli_stdout:
            self.text += line + '\n'

class Blockchain:

    def __init__(self, cli_stdout):
        self.text = ""
        for line in cli_stdout:
            self.text += line + '\n'

class Connections:

    def __init__(self, cli_stdout):
        self.text = ""
        for line in cli_stdout:
            self.text += line + '\n'

