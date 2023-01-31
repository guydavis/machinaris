import os
import re
import traceback

from api import app

PID_FILE = '/root/.chia/plotman/plotman.pid'

class PlottingSummary:

    def __init__(self, cli_stdout, plotman_pid):
        self.rows = []
        for line in cli_stdout:
            if not line.strip() or line.startswith("Total jobs") or line.startswith("Updated at") or line.startswith("Jobs in"):
                pass
            elif "plot id" in line.strip(): # The header row
                self.columns = line.replace('plot id', 'plot_id').strip().split()
                # Plotman has two columns both named 'tmp' so change the 2nd one to 'size'
                self.columns[8] = 'size'
            else: # Check for a plotting job row
                values = line.split()
                if len(values) > 1 and values[1] in ['chia', 'madmax', 'bladebit']:
                    if len(values) == len(self.columns) - 1:
                        app.logger.info("Bladebit job before: {0}".format(values))
                        values.insert(3, '-') # bladebit rows don't have a tmp directory
                        app.logger.info("Bladebit job after: {0}".format(values))
                    if len(values) == len(self.columns):
                        row = {}
                        i = 0
                        for i in range(len(self.columns)):
                            row[self.columns[i]] = values[i]
                            i += 1
                        self.rows.append(row)
                    else:
                        app.logger.info("Plotman status {0} values, expected {1}: {2}".format(len(values), len(self.columns), line))
                else:
                    app.logger.info("Plotman status without known 'plotter' value: {0}".format(line))
        self.calc_status()
        if plotman_pid:
            self.plotman_running = True
        else:
            self.plotman_running = False

    def calc_status(self):
        if len(self.rows) > 0:
            self.display_status = "Active"
        else:
            self.display_status = "Idle"       

class Transfer:

    def __init__(self, log_file, rsync_processes):
        self.log_file = log_file
        self.plot_id = ''
        self.k = 0  # k size like 31, 32, 34, etc
        self.size = 0  # total plot size in bytes
        self.source = '' # Full path to plot on plotter system
        self.type = '' # Either local or remote transfer
        self.dest = '' # Rsync destination path (local or remote)
        self.status = '' # One of "Transferring", "Complete", "Failed"
        self.rate = '' # Current or last transfer rate from rsync progress
        self.pct_complete = 0 # Percentage complete from rsync progress
        self.size_complete = '' # Human readable size transferred from rsync progress
        self.start_date = '' # Datetime the transfer started
        self.end_date = '' # Datetime the transfer ended (if successfully completed)
        self.duration = '' # H:M:S on transfer so far (or in total if completed)
        running_transfers = self.extract_running_transfers(rsync_processes)
        self.parse_transfer_log(log_file, running_transfers)

    def parse_transfer_log(self, log_file, running_transfers):
        if not os.path.exists(log_file):
            app.logger.info("No such transfer log file at {0}".format(log_file))
        with open(log_file) as f:
            for line in f.readlines():
                if line.startswith("Launching"):
                    if 'remote' in line:
                        self.type = 'Remote'
                    else:
                        self.type = 'Local'
                    if ' at ' in line:
                        self.start_date = line[line.index(' at ')+4:].strip()
                    else: # Old Plotman logs didn't include time until I enhanced, ignore them
                        self.log_file = None # indicates should be skipped
                elif line.startswith("Completed"):
                    self.end_date = line[line.index(' at ')+4:].strip()
                elif line.startswith("+ rsync"):
                    m = re.search("plot(?:-mmx)?-k(\d+)(?:-c\d)?-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\w+).plot", line)
                    if m:
                        self.plot_id = m.group(7)[:16].strip()
                        self.k = int(m.group(1).strip())
                    self.source = line.split(' ')[-2].strip()
                    self.dest = line.split(' ')[-1].strip()
                    try:
                        if os.path.exists(self.source):
                            self.size = os.path.getsize(self.source)
                    except Exception as ex:
                        app.logger.error("Failed to get size of: {0}".format(self.source))
                elif '/s ' in line:  # Rsync progress like "8.31G   7%   97.00MB/s    0:16:51"
                    [self.size_complete, self.pct_complete, self.rate, self.duration] = [str.strip() for str in line.split()][:4]
                    self.pct_complete = int(self.pct_complete[:-1]) # strip off the percent sign
            if self.pct_complete == 100 and self.end_date:
                self.status = "Complete"
            elif self.source in running_transfers:
                # Flag only this most recent transfer as running, any others earlier on same plot are failures
                self.status = "Transferring"
                running_transfers.remove(self.source)
            else: 
                self.status = "Failed"

    def extract_running_transfers(self, rsync_processes):
        running_transfers = []
        for process in rsync_processes:
            for piece in process.cmdline():
                if piece.startswith('/') and piece.endswith('.plot'):
                    running_transfers.append(piece)
        return running_transfers
