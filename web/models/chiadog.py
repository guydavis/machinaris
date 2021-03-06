import traceback

from web import app
from web.actions import worker

class Alerts:

    def __init__(self, alerts):
        self.rows = []
        for alert in alerts:
            try:
                w = worker.get_worker(alert.hostname)
                displayname = w.displayname
            except:
                app.logger.debug("Failed to find worker for hostname: {0}".format(alert.hostname))
                displayname = alert.hostname
            self.rows.append({
                'unique_id': alert.unique_id,
                'hostname': alert.hostname,
                'worker': displayname,
                'blockchain': alert.blockchain,
                'service': alert.service,
                'message': alert.message,
                'priority': alert.priority,
                'created_at': alert.created_at
            })