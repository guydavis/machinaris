import datetime
import json
import os
import traceback

from common.config import globals

from web import app

class Host:

    def __init__(self, hostname, displayname):
        self.hostname = hostname 
        self.displayname = displayname
        self.workers = []
    
    def plotting_status(self):
        status = "unknown"
        for worker in self.workers:
            if worker['plotting_status'] == 'running':
                status = "running"
            elif not status == 'running':
                status = worker['plotting_status']
        return status

    def archiving_status(self):
        status = "unknown"
        for worker in self.workers:
            if worker['archiving_status'] == 'running':
                status = "running"
            elif not status == 'running':
                status = worker['archiving_status']
        return status

    def farming_status(self):
        status = "unknown"
        for worker in self.workers:
            app.logger.info("{0} {1} ==> {2}".format(worker['displayname'], worker['blockchain'], worker['farming_status']))
            if worker['farming_status'] == 'farming':
                status = "farming"
            elif worker['farming_status'] == 'harvesting':
                status = "harvesting"
            elif not status in ['farming', 'harvesting']:
                status = worker['farming_status']
        return status

    def monitoring_status(self):
        status = "unknown"
        for worker in self.workers:
            if worker['monitoring_status'] == 'running':
                status = "running"
            elif not status == 'running':
                status = worker['monitoring_status']
        return status


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
            if 'blockchain_version' in config:
                other_versions += blockchain.capitalize() + ": " + config['blockchain_version'] + "<br/>"
        if 'chiadog_version' in config:
            other_versions += "Chiadog: " + config['chiadog_version'] + "<br/>"
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

    def status_if_responding(self, displayname, blockchain, connection_status, last_status):
        if connection_status == "Responding":
            return last_status
        app.logger.info("Oops! {0} ({1}) last connection status: {2}".format(displayname, blockchain, connection_status))
        return "offline"

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
                host.workers.append({
                    'hostname': worker.hostname,
                    'displayname': worker.displayname,
                    'config': json.loads(worker.config),
                })
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
                    'blockchain': worker.blockchain,
                    'displayname': worker.displayname,
                    'connection_status': worker.connection_status(),
                    'url': worker.url,
                    'port': worker.port,
                    'plotting_status': self.status_if_responding(worker.displayname, worker.blockchain, worker.connection_status(), worker.plotting_status()),
                    'archiving_status': self.status_if_responding(worker.displayname, worker.blockchain, worker.connection_status(), worker.archiving_status()),
                    'archiving_enabled': self.status_if_responding(worker.displayname, worker.blockchain, worker.connection_status(), worker.archiving_enabled()),
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
                    'farming_status': self.status_if_responding(worker.displayname, worker.blockchain, worker.connection_status(), worker.farming_status().lower()),
                    'monitoring_status': self.status_if_responding(worker.displayname, worker.blockchain, worker.connection_status(), worker.monitoring_status().lower())
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
                    'farming_status': self.status_if_responding(worker.displayname, worker.blockchain, worker.connection_status(), worker.farming_status().lower()),
                    'monitoring_status': self.status_if_responding(worker.displayname, worker.blockchain, worker.connection_status(), worker.monitoring_status().lower())
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
                    'farming_status': self.status_if_responding(worker.displayname, worker.blockchain, worker.connection_status(), worker.farming_status().lower()),
                    'monitoring_status': self.status_if_responding(worker.displayname, worker.blockchain, worker.connection_status(), worker.monitoring_status().lower())
                })
        filtered.sort(key=lambda w: w.displayname)
        return filtered
