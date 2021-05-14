from app import app

class PlottingSummary:

    def __init__(self, cli_stdout):
        self.rows = []
        for line in cli_stdout:
            if "plot id" in line.strip(): # The header row
                self.columns = line.replace('plot id', 'plot_id').strip().split()
            else: # A plotting row, so create as dictionary
                row = {}
                values = line.split()
                i = 0
                for i in range(len(self.columns)):
                    row[self.columns[i]] = values[i]
                    i += 1
                self.rows.append(row)
        self.calc_status()

    def calc_status(self):
        if len(self.rows) > 0:
            self.display_status = "Active"
        else:
            self.display_status = "Idle"