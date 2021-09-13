#!/bin/env bash
#
# Installs bladebit - A fast RAM-only, k32-only, Chia plotter.
# 416 GiB of RAM are needed. See https://github.com/harold-b/bladebit
# NOTE: During Docker image build on Github build servers, just clone the repo
#

BLADEBIT_BRANCH=master

# Checkout the project
cd /
git clone --recursive --branch ${BLADEBIT_BRANCH} https://github.com/harold-b/bladebit.git
