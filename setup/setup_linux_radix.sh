#!/bin/bash

git clone https://github.com/xlab-uiuc/emt-linux.git emt-linux-radix;
cd emt-linux-radix;
git checkout main;
cp configs/general_interface_radix_config .config;

make olddefconfig
make -j `nproc` LOCALVERSION=-gen-x86