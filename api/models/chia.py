import os
import re
import traceback

from datetime import datetime

from api import app
from common.utils import converters

# Treat *.plot files smaller than this as in-transit (copying) so don't count them
MINIMUM_K32_PLOT_SIZE_BYTES = 100 * 1024 * 1024

class FarmSummary:

    def __init__(self, cli_stdout=None, farm_plots=None):
        if cli_stdout:
            for line in cli_stdout:
                if "status" in line: 
                    self.calc_status(line.split(':')[1].strip())
                elif "Total chia farmed" in line:
                    self.total_chia = line.split(':')[1].strip()
                elif "Plot count" in line:
                    self.plot_count = line.split(':')[1].strip()
                elif "Total size of plots" in line:
                    self.plots_size = line.split(':')[1].strip()
                elif "Estimated network space" in line:
                    self.calc_netspace_size(line.split(':')[1].strip())
                elif "Expected time to win" in line:
                    self.time_to_win = line.split(':')[1].strip()
                elif "User transaction fees" in line:
                    self.transaction_fees = line.split(':')[1].strip()
                # TODO Handle Connection error lines from Harvester etc
        elif farm_plots:
            self.plot_count = 0
            bytes_size = 0
            for plot in farm_plots.rows:
                if plot['size'] > MINIMUM_K32_PLOT_SIZE_BYTES:
                    self.plot_count += 1
                    bytes_size += int(plot['size'])
                else:
                    app.logger.debug("Skipping inclusion of {0} size plot: {1}".format( \
                        converters.sizeof_fmt(plot['size'], plot['path'])))
            self.plots_size = converters.sizeof_fmt(bytes_size)
        else:
            raise Exception("Not provided either chia stdout lines or a list of plots.")

    def calc_status(self, status):
        self.status = status
        if self.status == "Farming":
            self.display_status = "Active"
        #elif self.status == "Not synced or not connected to peers":
        #    self.display_status = "<span style='font-size:.6em'>" + self.status + '</span>'
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
        
class FarmPlots:

     def __init__(self, entries):
        self.columns = ['plot_id', 'dir', 'plot', 'create_date', 'size']
        self.rows = []
        for st_ctime, st_size, path in entries:
            if not path.endswith(".plot"):
                app.logger.info("Skipping non-plot file named: {0}".format(path))
                continue
            dir,file=os.path.split(path)
            groups = re.match("plot-k(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\w+).plot", file)
            if not groups:
                app.logger.info("Invalid plot file name provided: {0}".format(file))
                continue
            plot_id = groups[7][:8]
            self.rows.append({ \
                'plot_id': plot_id, \
                'dir': dir,  \
                'file': file,  \
                'created_at': datetime.fromtimestamp(int(st_ctime)).strftime('%Y-%m-%d %H:%M:%S'), \
                'size': int(st_size) }) 

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

