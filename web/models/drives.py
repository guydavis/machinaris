import traceback

from flask_babel import _, lazy_gettext as _l

from web import app
from web.actions import worker

class Drives:

    def __init__(self, drives):
        self.rows = []
        for drive in drives:
            try:
                w = worker.get_worker(drive.hostname)
                displayname = w.displayname
            except:
                app.logger.debug("Failed to find worker for hostname: {0}".format(drive.hostname))
                displayname = drive.hostname
            self.rows.append({
                'serial_number': drive.serial_number,
                'hostname': drive.hostname,
                'worker': displayname,
                'blockchain': drive.blockchain,
                'model_family': drive.model_family,
                'device_model': drive.device_model,
                'device': drive.device,
                'status': drive.status,
                'type': drive.type,
                'comment': drive.comment,
                'temperature': drive.temperature,
                'power_on_hours': self.convert_hours_days_etc(drive.power_on_hours),
                'size_gibs': drive.size_gibs,
                'capacity': drive.capacity,
                'smart_info': drive.smart_info,
                'created_at': drive.created_at,
                'updated_at': drive.updated_at
            })

    def convert_hours_days_etc(self, hours):
        if hours < 24:
            return "{0} ".format(round(hours, 1)) + _('hours')
        if hours < 24 * 7:
            return "{0} ".format(round(hours/24, 1)) + _('days')
        if hours < 24 * 7 * 5:
            return "{0} ".format(round(hours/24/7, 1)) + _('weeks')
        if hours < 24 * 365:
            return "{0} ".format(round(hours/24/365*12, 1)) + _('months')
        return "{0} ".format(round(hours/24/365, 1)) + _('years')