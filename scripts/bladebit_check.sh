#!/bin/env bash
#
# Checks that Bladebit built on Github servers works.  If not, perhaps due
# to local hardware, then will re-build on container start on the specific machine.
#

/usr/bin/bladebit --version
if [[ $? -ne 0 ]]; then
    echo "Found broken bladebit from Github build.  Rebuilding on your local hardware now..."
    rm /usr/bin/bladebit && rm -rf /bladebit
    /machinaris/scripts/bladebit_install.sh
fi