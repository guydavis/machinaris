import os
import traceback

from web import app


class PlottingSummary:

    def __init__(self, plottings):
        self.columns = ['worker',
                        'plot_id',
                        'k',
                        'tmp',
                        'dst',
                        'wall',
                        'phase',
                        'size',
                        'pid',
                        'stat',
                        'mem',
                        'user',
                        'sys',
                        'io',
                        'created_at',
                        ]
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
                'user': plotting.user,
                'sys': plotting.sys,
                'io': plotting.io,
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
