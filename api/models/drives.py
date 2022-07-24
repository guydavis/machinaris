import os
import re
import traceback

from datetime import datetime

from api import app, utils
from common.config import globals

class DriveStatus:

    def __init__(self, device, device_type, device_comment, info):
        self.device = device
        self.type = device_type
        self.comment = device_comment
        self.smart_info = info  # From smartctl -a
        self.set_info_attributes(info.splitlines())

    def set_info_attributes(self, data):
        self.model_family = ''
        self.device_model = ''
        self.serial_number = ''
        self.size_gibs = None
        self.capacity = ''
        self.status = ''
        self.power_on_hours = None
        self.temperature = None
        for line in data:
            if line.strip().startswith('Model Family'):  # Sometimes present
                # Example: "Model Family:     Seagate BarraCuda 3.5"
                self.model_family = line.split(':')[1].strip()
            elif line.strip().startswith('Device Model'): # Sometimes present
                # Example: "Device Model:     ST8000DM004-2CX188"
                self.device_model = line.split(':')[1].strip()
            elif line.strip().startswith('Serial Number'):
                # Example: "Serial Number:    ZR106HWB"
                self.serial_number = line.split(':')[1].strip()
            elif line.strip().startswith('User Capacity'):
                # Example: "User Capacity:    8,001,563,222,016 bytes [8.00 TB]""
                size = line.split(':')[1].strip()
                self.size_gibs = round(float(int(size.split('bytes')[0].strip().replace(',', '')) / 1024 / 1024 / 1024), 3)
                self.capacity = size.split('bytes')[1].strip()[1:-1] # Drop square brackets
            elif line.strip().startswith('SMART overall-health self-assessment test result:'):
                # Example: "SMART overall-health self-assessment test result: PASSED"
                self.status = line.split(':')[1].strip()
            elif line.strip().startswith('SMART Health Status:'): # Seen if '-d scsi' passed incorrectly
                # Example: "SMART Health Status: OK"
                self.status = line.split(':')[1].strip().replace('OK', 'PASSED')
            elif 'Power_On_Hours' in line:
                # Example: "  9 Power_On_Hours          0x0032   092   092   000    Old_age   Always       -       7185 (119 239 0)"
                self.power_on_hours = line.split()[9].strip()
                if 'h' in self.power_on_hours:  # Sometimes value is '11479h+00m+00.000s', so strip off trailing, hours is fine
                    self.power_on_hours = self.power_on_hours.split('h')[0]
            elif 'Temperature_Celsius' in line:
                # Example: "194 Temperature_Celsius     0x0022   038   049   000    Old_age   Always       -       38 (0 21 0 0 0)"
                self.temperature = line.split()[9].strip()
            elif 'Current Drive Temperature:' in line:
                # Example: "Current Drive Temperature:     34 C"
                self.temperature = line.split(':')[1][:-1].strip()
        # Now print warning if missing fields
        if not self.model_family and not self.device_model:
            app.logger.info("Drive device {0} was missing Model information.  Have you set 'device_type: scsi' in drives_overrides.json when you don't need to?  Remove that and allow Machinaris to just: smartcl -a {0}".format(self.device))
