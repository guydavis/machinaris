import os
import traceback

from datetime import datetime

from web import app
from common.utils import converters

# Treat *.plot files smaller than this as in-transit (copying) so don't count them
MINIMUM_K32_PLOT_SIZE_BYTES = 100 * 1024 * 1024

class FarmSummary:

    def __init__(self, farms):
        self.status = "Unknown"
        self.plot_count = 0
        self.plots_size = 0
        self.total_chia = 0
        self.netspace_size = 0
        self.netspace_display_size = "?"
        self.expected_time_to_win = "Unknown"
        for farm in farms:
            self.plot_count += farm.plot_count
            self.plots_size += farm.plots_size
            if farm.mode == "fullnode":
                self.total_chia = farm.total_chia
                self.netspace_display_size = converters.gib_to_fmt(farm.netspace_size)
                self.netspace_size = farm.netspace_size
                self.status = farm.status
                self.expected_time_to_win = farm.expected_time_to_win
        self.plots_display_size = converters.gib_to_fmt(self.plots_size)
        self.calc_status(self.status)

    def calc_status(self, status):
        self.status = status
        if self.status == "Farming":
            self.display_status = "Active"
        else:
            self.display_status = self.status

class FarmPlots:

     def __init__(self, plots):
        self.columns = ['worker', 'plot_id',  'dir', 'plot', 'create_date', 'size']
        self.rows = []
        for plot in plots:
            self.rows.append({ \
                'worker': plot.hostname, \
                'plot_id': plot.plot_id, \
                'dir': plot.dir,  \
                'plot': plot.file,  \
                'create_date': plot.created_at, \
                'size': plot.size }) 


class BlockchainChallenges:

    def __init__(self, challenges):
        self.columns = ['hostname',
                        'challenge_id',
                        'plots_past_filter',
                        'proofs_found',
                        'time_taken',
                        'created_at',
                        ]
        self.rows = []
        for challenge in challenges:
            self.rows.append({
                'hostname': challenge.hostname,
                'challenge_id': challenge.challenge_id,
                'plots_past_filter': challenge.plots_past_filter,
                'proofs_found': challenge.proofs_found,
                'time_taken': challenge.time_taken,
                'created_at': challenge.created_at,
            })

class Wallets:

    def __init__(self, wallets):
        self.columns = ['hostname', 'details', 'updated_at']
        self.rows = []
        for wallet in wallets:
            updated_at = wallet.updated_at or datetime.now()
            self.rows.append({ \
                'hostname': wallet.hostname, \
                'details': wallet.details,
                'updated_at': wallet.updated_at }) 

class Keys:

    def __init__(self, keys):
        self.columns = ['hostname', 'details', 'updated_at']
        self.rows = []
        for key in keys:
            self.rows.append({ \
                'hostname': key.hostname, \
                'details': key.details,
                'updated_at': key.updated_at }) 

class Blockchains:

    def __init__(self, blockchains):
        self.columns = ['hostname', 'details', 'updated_at']
        self.rows = []
        for blockchain in blockchains:
            self.rows.append({ \
                'hostname': blockchain.hostname, \
                'details': blockchain.details,
                'updated_at': blockchain.updated_at }) 

class Connections:

    def __init__(self, connections):
        self.rows = []
        for connection in connections:
            self.rows.append({
                'hostname': connection.hostname,
                'details': connection.details
            })
    
    def parse(connections):
        # TODO Deal with connection listing from multiple machines
        connection = connections[0]
        self.conns = []
        for line in connection.details.split('\n'):
            try:
                if line.strip().startswith('Connections:'):
                    pass
                elif line.strip().startswith('Type'):
                    self.columns = line.lower().replace('last connect', 'last_connect') \
                        .replace('mib up|down', 'mib_up mib_down').strip().split()
                elif line.strip().startswith('-SB Height'):
                    pass
                else:
                    vals = line.strip().split()
                    #app.logger.debug(vals)
                    self.conns.append({
                        'type': vals[0],
                        'ip': vals[1],
                        'ports': vals[2],
                        'nodeid': vals[3].replace('...',''),
                        'last_connect': datetime.strptime( \
                            str(datetime.today().year) + ' ' + vals[4] + ' ' + vals[5] + ' ' + vals[6], 
                            '%Y %b %d %H:%M:%S'),
                        'mib_up': float(vals[7].split('|')[0]),
                        'mib_down': float(vals[7].split('|')[1])
                    })
            except:
                app.logger.info(traceback.format_exc())
