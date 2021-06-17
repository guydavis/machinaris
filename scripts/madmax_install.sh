#!/bin/env bash
#
# Installs chia-plotter (pipelined multi-threaded)
# See https://github.com/madMAx43v3r/chia-plotter
#

cd /
sudo apt install -y libsodium-dev cmake g++ git
git clone https://github.com/madMAx43v3r/chia-plotter.git 
cd chia-plotter
git submodule update --init
./make_devel.sh
./build/chia_plot --help
