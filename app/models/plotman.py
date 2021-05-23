import os
import traceback

from app import app

PID_FILE = '/root/.chia/plotman/plotman.pid'

class PlottingSummary:

    def __init__(self, cli_stdout, plotman_pid):
        self.rows = []
        for line in cli_stdout:
            if "plot id" in line.strip(): # The header row
                self.columns = line.replace('plot id', 'plot_id').strip().split()
                # Plotman has two columns both named 'tmp' so change the 2nd one to 'size'
                self.columns[6] = 'size'
            else: # A plotting row, so create as dictionary
                row = {}
                values = line.split()
                i = 0
                for i in range(len(self.columns)):
                    row[self.columns[i]] = values[i]
                    i += 1
                self.rows.append(row)
        self.calc_status()
        app.logger.debug("plotman_pid: {0}".format(plotman_pid))
        if plotman_pid:
            self.plotman_running = True
        else:
            self.plotman_running = False

    def calc_status(self):
        if len(self.rows) > 0:
            self.display_status = "Active"
        else:
            self.display_status = "Idle"       
