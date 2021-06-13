#!/bin/env bash
#
# Plotman introduced breaking config changes in v0.4+
#

echo 'Migrating Plotman...'

cd /root/.chia/plotman

mv plotman.yaml plotman_v0_3.yaml

# Start with new logging preamble
cat /machinaris/config/plotman_v0.4_preamble.yaml > plotman.yaml

# Remove old logging section from existing config
sed -e 's/^.*log:.*$//g' plotman_v0_3.yaml > plotman_end.yaml
sed -i -e 's/.*# One directory in which to store all plot job logs.*$//g' plotman_end.yaml
sed -i -e 's/.*# STDERR of all plot jobs).  In order to monitor progress, plotman.*$//g' plotman_end.yaml
sed -i -e 's/.*# reads these logs on a regular basis, so using a fast drive is.*$//g' plotman_end.yaml
sed -i -e "s/.*# recommended.  DON'T CHANGE THIS IN-CONTAINER PATH.*$//g" plotman_end.yaml

# Finally, append cleaned-up old config to new preamble
tee -a plotman.yaml > /dev/null < plotman_end.yaml
