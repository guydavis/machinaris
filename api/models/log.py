#
# Data from log reading and parsing
#

import re
import traceback

from api import app
from common.utils import converters

class Challenges:

    # Parse the provided most recent 5 lines of grepped output for challenges
    def __init__(self, cli_stdout):
        self.columns = [ 'challenge_id', 'plots_past_filter', 'proofs_found', 'time_taken', 'created_at']
        self.rows = []
        for line in cli_stdout:
            #app.logger.info(line)
            try:
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
