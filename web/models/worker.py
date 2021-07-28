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
            if 'chia_version' in config:
                other_versions += "Chia: " + config['chia_version'] + "<br/>"
            if 'chiadog_version' in config:
                other_versions += "Chiadog: " + config['chiadog_version'] + "<br/>"
            gc = globals.load()
            if gc['flax_enabled']:
                if 'flax_version' in config:
                    other_versions += "Flax: " + config['flax_version'] + "<br/>"
                if 'flaxdog_version' in config:
                    other_versions += "Flaxdog: " + config['flaxdog_version'] + "<br/>"
            if 'madmax_version' in config:
                other_versions += "Madmax: " + config['madmax_version'] + "<br/>"
            if 'plotman_version' in config:
                other_versions += "Plotman: " + config['plotman_version']
            worker.versions['components'] = other_versions

    def set_ping_response(self, response):
        self.ping_response = response
