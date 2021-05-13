from app import app

class PlottingSummary:

    def __init__(self, cli_stdout):
        app.logger.info("cli_stdout={0}".format(cli_stdout))
        self.plots = []
        for line in cli_stdout:
            app.logger.info(line)
            if "plot id" in line.strip(): # The header row
                self.header = line.replace('plot id', 'plot_id').strip().split()
                #app.logger.info(self.header)
            else: # A plotting row
                self.plots.append(line.split())
        #app.logger.info(self.plots)
        self.calc_status()

    def calc_status(self):
        if len(self.plots) > 0:
            self.display_status = "Active"
        else:
            self.display_status = "Idle"