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
