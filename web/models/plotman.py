import os
import traceback

from flask_babel import _, lazy_gettext as _l

from common.utils import converters
from web import app
from web.actions import worker as w

class PlottingSummary:

    def __init__(self, plottings):
        self.columns = ['worker',
                        'fork',
                        'plotter',
                        'plot_id',
                        'k',
                        'lvl',
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
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(plotting.hostname))
                displayname = w.get_worker(plotting.hostname).displayname
            except:
                app.logger.info("PlottingSummary.init(): Unable to find a worker with hostname '{0}'".format(plotting.hostname))
                displayname = plotting.hostname
            self.rows.append({
                'hostname': plotting.hostname,
                'fork': plotting.blockchain,
                'worker': displayname,
                'plotter': plotting.plotter,
                'plot_id': plotting.plot_id,
                'k': plotting.k,
                'lvl': plotting.lvl,
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

    def calc_status(self):
        if len(self.rows) > 0:
            self.display_status = _("Suspended")
            for row in self.rows:
                if row['stat'] != 'STP':
                    self.display_status = _("Active")
                    return
        else:
            self.display_status = _("Idle")

    def strip_trailing_slash(self, path):
        if path.endswith('/'):
            return path[:-1]
        return path

class ArchivingSummary:

    def __init__(self, transfers):
        self.columns = ['worker',
                        'fork',
                        'path',
                        'plot_id',
                        #'k',
                        #'size',
                        #'type',
                        'dest',
                        'status',
                        'pct',
                        'sent',
                        'rate',
                        'time',
                        'start',
                        #'end',
                        ]
        self.rows = []
        for transfer in transfers:
            try:
                app.logger.debug("Found worker with hostname '{0}'".format(transfer.hostname))
                displayname = w.get_worker(transfer.hostname).displayname
            except:
                app.logger.info("PlottingSummary.init(): Unable to find a worker with hostname '{0}'".format(transfer.hostname))
                displayname = transfer.hostname
            self.rows.append({
                'hostname': transfer.hostname,
                'fork': transfer.blockchain,
                'worker': displayname,
                'path': self.plot_path(transfer.source),
                'plot_id': transfer.plot_id,
                'k': transfer.k,
                'size': converters.sizeof_fmt(transfer.size),
                'type': transfer.type,
                'dest': transfer.dest,
                'status': transfer.status,
                'pct': "{0}%".format(transfer.pct_complete),
                'sent': transfer.size_complete,
                'rate': transfer.rate,
                'time': transfer.duration,
                'start': transfer.start_date,
                'end': transfer.end_date,
                'log_file': self.log_file_name(transfer.log_file),
            })

    def plot_path(self, source):
        if source and source.endswith('.plot'):
            return os.path.dirname(source)
        return ""
    
    def log_file_name(self, log_file_path):
        if log_file_path and log_file_path.endswith('.log'):
            return os.path.basename(log_file_path)
        return ""
