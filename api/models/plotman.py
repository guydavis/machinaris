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
                self.columns[7] = 'size'
            else: # Check for a plotting job row
                values = line.split()
                if values[1] in ['chia', 'madmax', 'bladebit']:
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
