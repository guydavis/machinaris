import json
import os
import traceback

from datetime import datetime

from common.config import globals

from web import app

class Host:

    def __init__(self, hostname, displayname):
        self.hostname = hostname 
        self.displayname = displayname
        self.workers = []

class WorkerSummary:

    def __init__(self, workers):
        self.hosts = []
        self.workers = workers
        for worker in workers:
            host = None
            for h in self.hosts:
                if h.displayname == worker.displayname:
                    host = h
            if not host:
                host = Host(worker.hostname, worker.displayname)
                self.hosts.append(host)
            self.set_worker_attributes(worker)

    def set_worker_attributes(self, worker):
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

    def set_ping_response(self, response):
        self.ping_response = response

    def fullnodes(self):
        filtered = []
        for worker in self.workers:
            if worker.mode == "fullnode":
                host = None
                for h in filtered:
                    if h.displayname == worker.displayname:
                        host = h
                if not host:
                    host = Host(worker.hostname, worker.displayname)
                    filtered.append(host)
        filtered.sort(key=lambda w: w.displayname)
        return filtered

    def plotters(self):
        filtered = []
        for worker in self.workers:
            if worker.mode == "fullnode" or "plotter" in worker.mode:
                host = None
                for h in filtered:
                    if h.displayname == worker.displayname:
                        host = h
                if not host:
                    host = Host(worker.hostname, worker.displayname)
                    filtered.append(host)
                host.workers.append({
                    'hostname': worker.hostname,
                    'displayname': worker.displayname,
                    'plotting_status': worker.plotting_status(),
                    'archiving_status': worker.archiving_status(),
                    'archiving_enabled': worker.archiving_enabled(),
                    'config': json.loads(worker.config),
                })
        filtered.sort(key=lambda w: w.displayname)
        return filtered

    def farmers(self):
        filtered = []
        for worker in self.workers:
            if worker.mode == "fullnode" or "farmer" in worker.mode:
                host = None
                for h in filtered:
                    if h.displayname == worker.displayname:
                        host = h
                if not host:
                    app.logger.info("Adding new host for {0}".format(worker.displayname))
                    host = Host(worker.hostname, worker.displayname)
                    filtered.append(host)
                host.workers.append({
                    'hostname': worker.hostname,
                    'displayname': worker.displayname,
                    'blockchain': worker.blockchain,
                    'farming_status': worker.farming_status().lower(),
                    'monitoring_status': worker.monitoring_status().lower()
                })
        filtered.sort(key=lambda w: w.displayname)
        return filtered

    def harvesters(self):
        filtered = []
        for worker in self.workers:
            if worker.mode == "fullnode" or "harvester" in worker.mode:
                host = None
                for h in filtered:
                    if h.displayname == worker.displayname:
                        host = h
                if not host:
                    app.logger.info("Adding new host for {0}".format(worker.displayname))
                    host = Host(worker.hostname, worker.displayname)
                    filtered.append(host)
                host.workers.append({
                    'hostname': worker.hostname,
                    'displayname': worker.displayname,
                    'blockchain': worker.blockchain,
                    'farming_status': worker.farming_status().lower(),
                    'monitoring_status': worker.monitoring_status().lower()
                })
        filtered.sort(key=lambda w: w.displayname)
        return filtered

    def farmers_harvesters(self):
        filtered = []
        for worker in self.workers:
            if worker.mode == "fullnode" or "farmer" in worker.mode or "harvester" in worker.mode:
                host = None
                for h in filtered:
                    if h.displayname == worker.displayname:
                        host = h
                if not host:
                    app.logger.info("Adding new host for {0}".format(worker.displayname))
                    host = Host(worker.hostname, worker.displayname)
                    filtered.append(host)
                host.workers.append({
                    'hostname': worker.hostname,
                    'displayname': worker.displayname,
                    'blockchain': worker.blockchain,
                    'farming_status': worker.farming_status().lower(),
                    'monitoring_status': worker.monitoring_status().lower()
                })
        filtered.sort(key=lambda w: w.displayname)
        return filtered
