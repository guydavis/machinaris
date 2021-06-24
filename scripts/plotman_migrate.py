#!/chia-blockchain/venv/bin/python
#
# Try to migrate older plotman.yaml to latest version
#

import logging
import os
import pathlib
import ruamel.yaml
import shutil
import sys
import time
import traceback
import yaml as sys_yaml

TARGET_VERSION = 2
PLOTMAN_SAMPLE = '/machinaris/config/plotman.sample.yaml'
PLOTMAN_EXAMPLE = '/root/.chia/plotman/plotman.sample.yaml'
PLOTMAN_CONFIG = '/root/.chia/plotman/plotman.yaml'

logging.basicConfig(level=logging.INFO)
yaml = ruamel.yaml.YAML()
yaml.indent(mapping=8, sequence=4, offset=2)
yaml.preserve_quotes = True

def migrate_config():
    new_config = yaml.load(pathlib.Path(PLOTMAN_SAMPLE))
    old_config = yaml.load(pathlib.Path(PLOTMAN_CONFIG))

    # Migrate selected settings over from the old config
    if 'directories' in old_config:
        for setting in ['tmp', 'tmp2']:
            if setting in old_config['directories']:
                new_config['directories'][setting] = old_config['directories'][setting]
    if 'scheduling' in old_config:
        for setting in ['tmpdir_stagger_phase_major', 'tmpdir_stagger_phase_minor', \
                'tmpdir_stagger_phase_limit', 'tmpdir_max_jobs', 'global_max_jobs', \
                    'global_stagger_m', 'polling_time_s']:
            if setting in old_config['scheduling']:
                new_config['scheduling'][setting] = old_config['scheduling'][setting]
    if 'plotting' in old_config:
        for setting in ['farmer_pk', 'pool_pk', 'type']:
            if setting in old_config['plotting']:
                new_config['plotting'][setting] = old_config['plotting'][setting]

    # Have to handle dst special because of trailing comment about archiving
    # which was completely overwriting new commented out section
    if 'directories' in old_config:
        if 'dst' in old_config['directories']:
            old_config_yaml = sys_yaml.safe_load(open(PLOTMAN_CONFIG, 'r'))
            # Must use other Yaml to get just the values in list, not old comments
            new_config['directories']['dst'] = old_config_yaml['directories']['dst']

    # Save a copy of the old config file first
    dst = "/root/.chia/plotman/plotman." + time.strftime("%Y%m%d-%H%M%S")+".yaml"
    shutil.copy(PLOTMAN_CONFIG, dst)
    # Then save the migrated config
    yaml.dump(new_config, pathlib.Path(PLOTMAN_CONFIG))

if __name__ == "__main__":
    try:
        shutil.copy(PLOTMAN_SAMPLE, PLOTMAN_EXAMPLE) # Always place latest example file
        if not os.path.exists(PLOTMAN_CONFIG):
            print("No existing plotman config found, so copying sample to: {0}".format(PLOTMAN_CONFIG))
            shutil.copy(PLOTMAN_SAMPLE, PLOTMAN_CONFIG)
        # Check for config version
        config = yaml.load(pathlib.Path(PLOTMAN_CONFIG))
        if 'version' in config:
            version =  config["version"][0]
        else:
            version = 0
        if version != TARGET_VERSION:
            print("Migrating plotman.yaml as found version: {0}".format(version))
            migrate_config()
    except:
        print(traceback.format_exc())