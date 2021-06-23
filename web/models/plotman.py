import os
import traceback

from web import app


class PlottingSummary:

    def __init__(self, plottings):
        self.columns = ['worker',
                        'plotter',
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
                        'io'
                        ]
        self.rows = []
        for plotting in plottings:
            self.rows.append({
                'worker': plotting.hostname,
                'plotter': plotting.plotter,
                'plot_id': plotting.plot_id,
                'k': plotting.k,
                'tmp': self.strip_trailing_slash(plotting.tmp),
                'dst': self.strip_trailing_slash(plotting.dst),
                'wall': plotting.wall,
                'phase': plotting.phase,
                'size': plotting.size,
                'pid': plotting.pid,
                'stat': plotting.stat,
                'mem': plotting.mem,
                'user': plotting.user,
                'sys': plotting.sys,
                'io': plotting.io
            })
        self.calc_status()
        if True:
            self.plotman_running = True
        else:
            self.plotman_running = False

    def calc_status(self):
        if len(self.rows) > 0:
            self.display_status = "Suspended"
            for row in self.rows:
                if row['stat'] != 'STP':
                    self.display_status = "Active"
                    return
        else:
            self.display_status = "Idle"

    def strip_trailing_slash(self, path):
        if path.endswith('/'):
            return path[:-1]
        return path
