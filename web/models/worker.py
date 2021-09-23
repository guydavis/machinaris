import json
import os
import traceback

from datetime import datetime

from common.config import globals

from web import app

class WorkerSummary:

    def __init__(self, workers):
        self.workers = workers
        self.fullnodes = []
        self.plotters = []
        self.farmers = []
        self.harvesters = []
        self.farmers_harvesters = []
        for worker in workers:
            if worker.mode == "fullnode" or "plotter" in worker.mode:
                self.plotters.append(worker)
            if worker.mode == "fullnode" or "farmer" in worker.mode:
                self.farmers.append(worker)
            if worker.mode == "fullnode" or "harvester" in worker.mode:
                self.harvesters.append(worker)
            if worker.mode == "fullnode" or "harvester" or "farmer" in worker.mode:
                self.farmers_harvesters.append(worker)
            if worker.mode == "fullnode":
                self.fullnodes.append(worker)
            config = json.loads(worker.config)
            worker.versions = {}
            if 'machinaris_version' in config:
                worker.versions['machinaris'] = config['machinaris_version']
            other_versions = ""
            gc = globals.load()
            if 'bladebit_version' in config:
                other_versions += "Bladebit: " + config['bladebit_version'] + "<br/>"
            if not 'enabled_blockchains' in config:  # Default if missing from old records
                config['enabled_blockchains'] = 'chia'
            for blockchain in config['enabled_blockchains']:
                if '{0}_version' in config:
                    other_versions += blockchain.capitalize() + ": " + config['{0}_version'] + "<br/>"
                if '{0}dog_version' in config:
                    other_versions += blockchain.capitalize() + "dog: " + config['{0}dog_version'] + "<br/>"
            if 'madmax_version' in config:
                other_versions += "Madmax: " + config['madmax_version'] + "<br/>"
            if 'plotman_version' in config:
                other_versions += "Plotman: " + config['plotman_version']
            worker.versions['components'] = other_versions
            if 'now' in config:
                worker.time_on_worker = config['now']
            else:
                worker.time_on_worker = '?'
            if not worker.port:  # Old records
                worker.port = 8927
        self.plotters.sort(key=lambda w: w.displayname)
        self.farmers.sort(key=lambda w: w.displayname)
        self.harvesters.sort(key=lambda w: w.displayname)
        self.fullnodes.sort(key=lambda w: w.displayname)

    def set_ping_response(self, response):
        self.ping_response = response
