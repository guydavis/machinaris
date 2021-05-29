#!/bin/env bash
#
# Only if PATCH_CHIAPOS is set, when building the image tagged with ':chiapos' 
# Patch for faster plotting, on some systems with newer/fast CPUs
# See https://github.com/guydavis/machinaris/wiki/Releases#chiapos 
#

PATCH_CHIAPOS=$1
echo "PATCH_CHIAPOS=${PATCH_CHIAPOS}"
if [[ $PATCH_CHIAPOS = 'true' ]]; then
    echo 'Patching with Chiapos...'
    cd /chia-blockchain
    curl -o install_multithreaded_chiapos.sh https://gist.githubusercontent.com/SippieCup/8420c831ffcd74f4c4c3c756d1bda912/raw/4be54e136f3f7c070f320e935e883e5ef4c7141d/install_multithreaded_chiapos.sh
    chmod a+x install_multithreaded_chiapos.sh
    ./install_multithreaded_chiapos.sh /chia-blockchain
else
    echo 'Not patching for chiapos. Leaving Chia binaries as stock for main release.'
fi