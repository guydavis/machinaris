#!/bin/env bash
#
# Installs bladebit - A fast RAM-only, k32-only, Chia plotter.
# 416 GiB of RAM are needed. See https://github.com/harold-b/bladebit
#
# Can't acutally build on Github servers, must build on each target system 
# during container launch, otherwise get all sorts of errors.
#

BLADEBIT_BRANCH=master

cd /
git clone --recursive --branch ${BLADEBIT_BRANCH} https://github.com/Chia-Network/bladebit.git
