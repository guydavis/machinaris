#!/bin/env bash
#
# As the official Docker image is out of date, this performs an upgrade install of latest Chia
#

echo 'Upgrading Chia...'

cd /chia-blockchain
rm -f entrypoint.sh
. ./activate
chia stop -d all
deactivate
git fetch
git stash
git checkout latest
git reset --hard FETCH_HEAD

# If you get RELEASE.dev0 then delete the package-lock.json in chia-blockchain-gui and install.sh again

git status

# git status should say "nothing to commit, working tree clean", 
# if you have uncommitted changes, RELEASE.dev0 will be reported.

sh install.sh

. ./activate

chia init

deactivate
