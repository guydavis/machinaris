import os
import traceback

from datetime import datetime

from web import app

class WorkerSummary:

    def __init__(self, workers):
        self.workers = workers
        self.fullnodes = []
        self.plotters = []
        self.farmers = []
        self.harvesters = []
        for worker in workers:
            if worker.mode == "fullnode" or "plotter" in worker.mode:
                self.plotters.append(worker)
            if worker.mode == "fullnode" or "farmer" in worker.mode:
                self.farmers.append(worker)
            if worker.mode == "fullnode" or "harvester" in worker.mode:
                self.harvesters.append(worker)
            if worker.mode == "fullnode":
                self.fullnodes.append(worker)
