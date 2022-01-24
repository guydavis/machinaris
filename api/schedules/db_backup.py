#
# Optionally performs a blockchain database backup.
# Always performs a blockchain services stop/start as well.
#


import os
import subprocess

from api import app
from common.config import globals
from api.commands import chia_cli

def execute():
    blockchain = globals.enabled_blockchains()[0]
    if blockchain == 'mmx':
        return  # Only Chia+forks for now
    chia_binary = globals.get_blockchain_binary(blockchain)
    # TODO Optionally perform a database backup with the blockchain stopped for consistency
    app.logger.info("Executing blockchain restart for {0}...".format(chia_binary))
    try:
        chia_cli.start_farmer(blockchain)
    except Exception as ex:
        app.logger.info("Failed to restart farmer because {0}.".format(str(ex)))
