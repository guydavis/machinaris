#!/bin/env bash
#
# Starts Plotman, when AUTO_PLOT/AUTO_ARCHIVE are enabled, on a Chia/Chives/MMX/Gigahorse fullnode or a plotter instance
#

if [[ (${mode} =~ ^fullnode.*  || ${mode} =~ "plotter") && (${blockchains} == 'chia' || ${blockchains} == 'chives' || ${blockchains} == 'mmx' || ${blockchains} == 'gigahorse') ]]; then
    # Start plotting automatically if requested (not the default)
    if [ ${AUTO_PLOT,,} = "true" ]; then
        nohup plotman plot >> /root/.chia/plotman/logs/plotman.log 2>&1 &
    fi
    # Start archiving automatically if requested (not the default)
    if [ ${AUTO_ARCHIVE,,} = "true" ]; then
        nohup plotman archive >> /root/.chia/plotman/logs/archiver.log 2>&1 &
    fi
fi