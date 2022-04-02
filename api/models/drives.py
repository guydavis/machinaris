import os
import re
import traceback

from datetime import datetime

from api import app, utils
from common.config import globals

class DriveStatus:

    def __init__(self, device_line, info):
        # First parse the single device line from smartctl --scan
        # Example "/dev/sda -d sat # /dev/sda [SAT], ATA device"
        values = device_line.split('#')
        self.comment = values[1].strip()
        values = values[0].split('-d')
        self.device = values[0].strip()
        self.type = values[1].strip()
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
            if line.startswith('Model Family'):
                # Example: "Model Family:     Seagate BarraCuda 3.5"
                self.model_family = line.split(':')[1].strip()
            elif line.startswith('Device Model'):
                # Example: "Device Model:     ST8000DM004-2CX188"
                self.device_model = line.split(':')[1].strip()
            elif line.startswith('Serial Number'):
                # Example: "Serial Number:    ZR106HWB"
                self.serial_number = line.split(':')[1].strip()
            elif line.startswith('User Capacity'):
                # Example: "User Capacity:    8,001,563,222,016 bytes [8.00 TB]""
                size = line.split(':')[1].strip()
                self.size_gibs = round(float(int(size.split('bytes')[0].strip().replace(',', '')) / 1024 / 1024 / 1024), 3)
                self.capacity = size.split('bytes')[1].strip()[1:-1] # Drop square brackets
            elif line.startswith('SMART overall-health self-assessment test result:'):
                # Example: "SMART overall-health self-assessment test result: PASSED"
                self.status = line.split(':')[1].strip()
            elif 'Power_On_Hours' in line:
                # Example: "  9 Power_On_Hours          0x0032   092   092   000    Old_age   Always       -       7185 (119 239 0)"
                self.power_on_hours = line.split()[9].strip()
            elif 'Temperature_Celsius' in line:
                # Example: "194 Temperature_Celsius     0x0022   038   049   000    Old_age   Always       -       38 (0 21 0 0 0)"
                self.temperature = line.split()[9].strip()
