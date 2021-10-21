#
# Handle dismissable warnings to the user
#

import datetime
import os

from flask import flash, url_for
from configparser import ConfigParser

from web import app

DISMISSED_SECTION = 'dismissed'
WARNINGS_PATH = '/root/.chia/machinaris/config/warnings.ini'

# Warning if the mnemonic file is still on disk after initial setup (key add)
def check_mnemonic_delete(msg):
    found_mnemonic = False
    try:
        for key_path in os.environ['keys'].split(':'):
            if os.path.exists(key_path):
                found_mnemonic = True
                app.logger.info("Found mnemonic key file at: {0}".format(key_path))
    except Exception as ex:
        app.logger.error("Failed to check for presence of mnemonic text files due to {0}".format(str(ex)))
    if found_mnemonic:
        flash(msg.format(url_for("index")), 'warning')
    return found_mnemonic

# Always recommend a cold wallet until they dismiss it
def check_cold_wallet(msg):
    flash(msg.format(url_for("index")), 'warning')
    return True

WARNINGS = {
    'mnemonic_delete': [check_mnemonic_delete, """
            <a class="btn btn-primary" style="float:right; margin-left:20px" role="button"href="{0}?mnemonic_delete=dismiss">Dismiss Warning</a>
                Head\'s up! Security best practice is to delete your mnemonic.txt after first launch. 
                Details on the <a target="_blank" href="https://github.com/guydavis/machinaris/wiki/Keys#deleting-mnemonic-off-disk">wiki</a>.
                Please ensure you have safely recorded your mnemonic passphrase (24 words) before deleting!
                """],
    'cold_wallet': [check_cold_wallet, """
            <a class="btn btn-primary" style="float:right; margin-left:20px" role="button"href="{0}?cold_wallet=dismiss">Dismiss Warning</a>
                Machinaris uses an online wallet for farming.  It is strongly recommended that you eventually use a cold wallet for your Chia payout instructions.
                Tutorial on the <a target="_blank" href="https://github.com/guydavis/machinaris/wiki/Keys#using-a-cold-wallet">wiki</a>.
                Please add "Setup a Cold Wallet" to your To-Do list!
                """],
}

def load_warnings():
    try:
        config = ConfigParser()
        config.read(WARNINGS_PATH)
        return config
    except Exception as ex:
        app.logger.info("Unable to open warnings file at: {0}".format(WARNINGS_PATH))
    return None

def check_warnings(args):
    if not os.path.exists(WARNINGS_PATH):
        app.logger.info('Skipping warnings as no file found, so will now create one at: {0}'.format(WARNINGS_PATH))
        open(WARNINGS_PATH, 'a').close()  # Create empty file
        return # No warnings on very first Summary page load.

    config = load_warnings()

    # Now check if any warnings were dismissed by user
    updated = False
    for key in WARNINGS:
        if args.get(key) == "dismiss":
            if not config.has_section(DISMISSED_SECTION):
                config.add_section(DISMISSED_SECTION)
            config.set(DISMISSED_SECTION, key, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            updated = True
        elif config.has_option(DISMISSED_SECTION, key):
            app.logger.debug("Warning skipped as already dismissed by user: {0}".format(key))
        else:
            warning = WARNINGS[key]
            handler = warning[0]
            message = warning[1]
            handler(message)
    if updated:
        with open(WARNINGS_PATH, 'w') as f:
            config.write(f)
