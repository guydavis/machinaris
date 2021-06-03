import os
import traceback

from web import app

PID_FILE = '/root/.chia/plotman/plotman.pid'

class PlottingSummary:

    def __init__(self, plottings):
        self.rows = []
        for plotting in plottings:
            self.rows.append({
                'worker': plotting.hostname,
                'plot_id': plotting.plot_id,
                'k': plotting.k,
                'tmp': plotting.tmp,
                'dst': plotting.dst,
                'wall': plotting.wall,
                'phase': plotting.phase,
                'size': plotting.size,
                'pid': plotting.pid,
                'stat': plotting.stat,
                'mem': plotting.mem,
                'user': plotting.stat,
                'sys': plotting.stat,
                'io': plotting.stat,
                'created_at': plotting.created_at,
            })
        self.calc_status()
        if True:
            self.plotman_running = True
        else:
            self.plotman_running = False

    def calc_status(self):
        if len(self.rows) > 0:
            self.display_status = "Active"
        else:
            self.display_status = "Idle"       
