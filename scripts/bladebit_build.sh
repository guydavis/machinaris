#!/bin/env bash
#
# At container launch on target user's system, this builds the bladebit
# codebase checked out on Github servers during image creation.  Due to
# issues with illegal instructions bladebit must be built on hardware it
# runs on. 
#

cd /bladebit
mkdir -p build && cd build
cmake ..
cmake --build . --target bladebit --config Release
ln -s /bladebit/build/bladebit /usr/bin/bladebit
cd /
echo "Bladebit version: "`bladebit --version`
