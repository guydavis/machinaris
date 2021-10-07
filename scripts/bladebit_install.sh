#!/bin/env bash
#
# Installs bladebit - A fast RAM-only, k32-only, Chia plotter.
# 416 GiB of RAM are needed. See https://github.com/harold-b/bladebit
#

BLADEBIT_BRANCH=master

cd /
git clone --recursive --branch ${BLADEBIT_BRANCH} https://github.com/harold-b/bladebit.git

cd /bladebit
mkdir -p build && cd build
cmake ..
cmake --build . --target bladebit --config Release
make install
cp ./bladebit /usr/bin/bladebit
cd .. && rm -r ./build
echo "Bladebit version: "`bladebit --version`
