from datetime import datetime

from app import app
from app import utils

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
                    self.plot_size = line.split(':')[1].strip()
                elif "Estimated network space" in line:
                    self.calc_network_size(line.split(':')[1].strip())
                elif "Expected time to win" in line:
                    self.time_to_win = line.split(':')[1].strip()
                elif "User transaction fees" in line:
                    self.transaction_fees = line.split(':')[1].strip()
                # TODO Handle Connection error lines from Harvestor etc
        elif farm_plots.rows:
            self.plot_count = len(farm_plots.rows)
            bytes_size = 0
            for plot in farm_plots.rows:
                bytes_size += int(plot['size'])
            self.plot_size = utils.sizeof_fmt(bytes_size)
        else:
            raise Exeption("Not provided either chia stdout lines or a list of plots.")

    def calc_status(self, status):
        self.status = status
        if self.status == "Farming":
            self.display_status = "Active"
        #elif self.status == "Not synced or not connected to peers":
        #    self.display_status = "<span style='font-size:.6em'>" + self.status + '</span>'
        else:
            self.display_status = self.status

    def calc_network_size(self, network_size):
        self.network_size = network_size
        try:
            size_value, size_unit = network_size.split(' ')
            if float(size_value) > 1000 and size_unit == 'PiB':
                self.display_network_size = "{:0.3f} EiB".format(float(size_value) / 1000)
            else:
                self.display_network_size = self.network_size
        except:
            app.logger.info("Unable to split network size value: {0}".format(network_size))
            self.display_network_size = self.network_size
        
    def __str__(self): 
        return "%s plots with %s chia taking up %s of total netspace: %s" % \
            (self.plot_count, self.total_chia, self.plot_size, self.network_size)

class FarmPlots:

     def __init__(self, entries):
        self.columns = ['dir', 'plot', 'create_date', 'size']
        self.rows = []
        for st_ctime, st_size, path in entries:
            self.rows.append({ 'dir': '/plots',  \
                'plot': path[len('/plots/'): ],  \
                'create_date': datetime.utcfromtimestamp(int(st_ctime)).strftime('%Y-%m-%d %H:%M:%S'), \
                'size': int(st_size) }) 

class Wallet:

    def __init__(self, cli_stdout):
        self.text = ""
        for line in cli_stdout:
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