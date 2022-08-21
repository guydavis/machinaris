#
# Data from log reading and parsing
#

import re
import traceback

from api import app
from common.utils import converters

class Challenges:

    # Parse the provided most recent lines of grepped output for challenges
    def __init__(self, cli_stdout, blockchain):
        self.columns = [ 'challenge_id', 'plots_past_filter', 'proofs_found', 'time_taken', 'created_at']
        self.rows = []
        for line in cli_stdout:
            #app.logger.info(line)
            try:
                if blockchain == 'mmx':
                    self.rows.append({
                        'challenge_id': re.search('eligible for height (\d+)', line, re.IGNORECASE).group(1),
                        'plots_past_filter': str(re.search('INFO:\s*(\d+) plots were eligible', line, re.IGNORECASE).group(1)),
                        'proofs_found': 0, # TODO What does log line with a proof look like?
                        'time_taken': str(re.search('took ([0-9]+\.?[0-9]*(?:[Ee]\ *-?\ *[0-9]+)?) sec', line, re.IGNORECASE).group(1)) + ' secs',
                        'created_at': line[:19]  # example at line start: 2022-01-25 10:14:33
                    })
                else: # All Chia forks
                    self.rows.append({
                        'challenge_id': re.search('eligible for farming (\w+)', line, re.IGNORECASE).group(1) + '...',
                        'plots_past_filter': str(re.search('INFO\s*(\d+) plots were eligible', line, re.IGNORECASE).group(1)) + \
                            '/' + str(re.search('Total (\d+) plots', line, re.IGNORECASE).group(1)),
                        'proofs_found': int(re.search('Found (\d+) proofs', line, re.IGNORECASE).group(1)),
                        'time_taken': str(re.search('Time: (\d+\.?\d*) s.', line, re.IGNORECASE).group(1)) + ' secs',
                        'created_at': line.split()[0].replace('T', ' ')
                    })
            except:
                app.logger.info("Failed to parse challenge line: {0}".format(line))
                app.logger.info(traceback.format_exc())
        self.rows.reverse()

class Partials:

    # Parse the provided most recent lines for partials.  Grep grabs 2 lines (partial submit and response) per.
    def __init__(self, cli_stdout):
        self.columns = [ 'challenge_id', 'plots_past_filter', 'proofs_found', 'time_taken', 'created_at']
        self.rows = []
        launcher_id = None
        for line in cli_stdout:
            try:
                if "Submitting partial" in line:
                    app.logger.debug(line)
                    created_at = line.split()[0].replace('T', ' ')
                    launcher_id = re.search('partial for (\w+) to', line, re.IGNORECASE).group(1)
                    pool_url = re.search('to (.*)$', line, re.IGNORECASE).group(1)
                elif "Pool response" in line and launcher_id:
                    pool_response = line[line.index('{'):]
                    self.rows.append({
                        'launcher_id': launcher_id,
                        'pool_url': pool_url.strip(),
                        'pool_response': pool_response,
                        'created_at': created_at
                    })
                    created_at = None
                    launcher_id = None
                    pool_url = None
            except:
                app.logger.info("Failed to parse partial line: {0}".format(line))
                app.logger.info(traceback.format_exc())
        self.rows.reverse()

class Blocks:

    # Parse the provided most recent lines for farmed blocks.
    def __init__(self, blockchain, cli_stdout):
        self.columns = [ 'challenge_id', 'plot_files', 'proofs_found', 'time_taken', 'farmed_block', 'created_at']
        self.rows = []
        if len(cli_stdout) == 0:
            return # Nothing to processs as no farmed blocks found in this log file
        if blockchain == 'mmx':
            self.parse_mmx(cli_stdout) 
        else:
            self.parse_chia(cli_stdout) 

    def parse_chia(self, cli_stdout):
        plot_files = []
        challenge_id = plots_past_filter = proofs_found = time_taken = farmed_block = created_at = None
        cli_stdout.append('--') # add a trailing -- to force last parse
        for line in cli_stdout:
            try:
                #app.logger.info(line)
                if "proofs in" in line:
                    plot_files.append(re.search('proofs in (.*) in (\d+\.?\d*) s$', line, re.IGNORECASE).group(1))
                elif "eligible for farming" in line:
                    challenge_id = re.search('eligible for farming (\w+)', line, re.IGNORECASE).group(1)
                    plots_past_filter = str(re.search('INFO\s*(\d+) plots were eligible', line, re.IGNORECASE).group(1)) + \
                            '/' + str(re.search('Total (\d+) plots', line, re.IGNORECASE).group(1))
                    proofs_found = int(re.search('Found (\d+) proofs', line, re.IGNORECASE).group(1))
                    time_taken = str(re.search('Time: (\d+\.?\d*) s.', line, re.IGNORECASE).group(1)) + ' secs'
                elif "Farmed unfinished_block" in line:
                    created_at =  line[:line.rfind(':')].split()[0].replace('T', ' ')
                    if "debug.log:" in created_at:
                        created_at = created_at[(created_at.index('debug.log:') + len('debug.log:')):]
                    elif "debug.log.1:" in created_at:
                        created_at = created_at[(created_at.index('debug.log.1:') + len('debug.log.1:')):]
                    farmed_block = re.search('Farmed unfinished_block (\w+)', line, re.IGNORECASE).group(1)
                elif "--" == line:
                    if challenge_id and plots_past_filter and proofs_found and time_taken and farmed_block:
                        self.rows.append({
                            'challenge_id': challenge_id,
                            'plot_files': ','.join(plot_files),
                            'plots_past_filter': plots_past_filter,
                            'proofs_found': proofs_found,
                            'time_taken': time_taken,
                            'farmed_block': farmed_block,
                            'created_at': created_at
                        })
                        app.logger.debug(self.rows)
                        plots_past_filter = proofs_found = time_taken = farmed_block = None
                        plot_files = []
                    else:
                        app.logger.info("challenge_id: {0}".format(challenge_id))
                        app.logger.info("plot_files: {0}".format(plot_files))
                        app.logger.info("plots_past_filter: {0}".format(plots_past_filter))
                        app.logger.info("proofs_found: {0}".format(proofs_found))
                        app.logger.info("time_taken: {0}".format(time_taken))
                        app.logger.info("created_at: {0}".format(created_at))
                        app.logger.info("Missing farmed blocks data for farmed_block {0}".format(farmed_block))
            except:
                app.logger.info("Failed to parse blocks line: {0}".format(line))
                app.logger.info(traceback.format_exc())
        self.rows.reverse()

    def parse_mmx(self, cli_stdout):
        # Single Line - Example: 2022-07-18 03:01:58 [Node] INFO: Created block at height 503229 with: ntx = 2, score = 10998, reward = 0.505957 MMX, nominal = 0.501956 MMX, fees = 0.008 MMX, took 0.037 sec
        for line in cli_stdout:
            try:
                #app.logger.info(line)
                time_taken = str(re.search('took (\d+\.?\d*) sec', line, re.IGNORECASE).group(1)) + ' secs'
                created_at =  "{0}.000".format(line[:19])
                farmed_block = re.search('Created block at height (\d+)', line, re.IGNORECASE).group(1)
                self.rows.append({
                    'challenge_id': '',
                    'plot_files': '',
                    'plots_past_filter': '',
                    'proofs_found': 1,
                    'time_taken': time_taken,
                    'farmed_block': farmed_block,
                    'created_at': created_at
                })
                #app.logger.info(self.rows)
            except:
                app.logger.info("Failed to parse MMX blocks line: {0}".format(line))
                app.logger.info(traceback.format_exc())
