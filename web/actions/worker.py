#
# Actions around managing distributed workers and their status.
#

import datetime
import os
import psutil
import re
import signal
import shutil
import socket
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash

from web import app, db
from common.models import workers as w
from common.config import globals
from web.models.worker import WorkerSummary

def load_worker_summary():
    workers = db.session.query(w.Worker).all()
    return WorkerSummary(workers)
