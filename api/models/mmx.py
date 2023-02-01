import os
import re
import traceback

from datetime import datetime

from api import app, utils
from common.config import globals
from common.utils import converters

class FarmSummary:

    def __init__(self, cli_stdout, blockchain):
            self.plot_count = 0
            self.plots_size = 0
            for line in cli_stdout:
                m = re.match('^K(\d+): (\d+) plots$', line)
                if m:
                    self.plot_count += int(m.group(2))
                elif line.startswith('Total size'):
                    self.plots_size = line.strip().split(':')[1].strip()
                # For now, treating the wallet balance as 100% farmed until better approach is found
                elif line.startswith('Balance'):  
                    self.total_coins = line.split(':')[1].strip().split(' ')[0].strip()
                elif line.startswith('Netspace'): # Example: Netspace:   88.3439 PB (99.9 % physical)
                    self.calc_netspace_size(line.split(':')[1].strip().split('(')[0].strip())
                elif line.startswith('Synced'):
                    if 'Yes' == line.split(':')[1].strip():
                        self.calc_status('Farming')
                    elif 'No' == line.split(':')[1].strip():
                        self.calc_status('Syncing')
                    else:
                        self.calc_status(line.strip())
            self.time_to_win = self.calc_mmx_etw(self.netspace_size, self.plots_size)
            #app.logger.info("MMX ETW_STR: {0}".format(self.time_to_win))

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
            app.logger.info("Unable to split network size value: {0}".format(netspace_size))
            self.display_netspace_size = self.netspace_size
    
    def calc_mmx_etw(self, netspace_size, plots_size):
        MMX_BLOCKS_PER_MIN = globals.get_blocks_per_day('mmx') / (24 * 60)
        #app.logger.info("MMX_BLOCKS_PER_MIN: {0}".format(MMX_BLOCKS_PER_MIN))
        plots_size_gib = converters.str_to_gibs(plots_size)
        #app.logger.info("MMX PLOTS_SIZE: {0}".format(plots_size_gib))
        netspace_size_gib = converters.str_to_gibs(netspace_size)
        #app.logger.info("MMX NETSPACE_SIZE: {0}".format(netspace_size_gib))
        if plots_size_gib > 0:
            etw_mins = round(netspace_size_gib / plots_size_gib /  MMX_BLOCKS_PER_MIN)
            #app.logger.info("MMX ETW_MINS: {0}".format(etw_mins))
            return converters.format_minutes(etw_mins)
        return "" # Zero plots, so basically never

class HarvesterSummary:

    def __init__(self):
        self.status = "Harvesting" # TODO Check for harvester status via MMX somehow (logs or cmds)

class FarmPlots:

     def __init__(self, entries):
        hostname = utils.get_hostname()
        self.columns = ['hostname', 'plot_id', 'dir', 'file', 'filename', 'type', 'create_date', 'size']
        self.rows = []
        for st_ctime, st_size, path in entries:
            if not path.endswith(".plot"):
                app.logger.info("Skipping non-plot file named: {0}".format(path))
                continue
            dir,file=os.path.split(path)
            groups = re.match("plot-mmx-k(\d+)(-c\d)?-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\w+).plot", file)
            if not groups:
                app.logger.info("Invalid plot file name provided: {0}".format(file))
                continue
            plot_id = groups[7][:8]
            self.rows.append({ \
                'hostname': hostname, \
                'plot_id': plot_id, \
                'dir': dir,  \
                'file': file, \
                'filename': path,  \
                'type': 'solo', \
                'created_at': datetime.fromtimestamp(int(st_ctime)).strftime('%Y-%m-%d %H:%M:%S'), \
                'file_size': int(st_size) }) 

class Wallet:

    def __init__(self, cli_stdout):
        self.text = ""
        lines = cli_stdout.split('\n')
        for line in lines:
            #app.logger.info("WALLET LINE: {0}".format(line))
            if "No online" in line or \
                "skip restore from backup" in line or \
                "own backup file" in line or \
                "SIGWINCH" in line:
                continue
            self.text += line + '\n'

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

