#!/bin/bash

git clone https://github.com/xlab-uiuc/emt-linux.git emt-linux-fpt-L4L3L2L1;
cd emt-linux-fpt-L4L3L2L1;
git checkout FPT;
cp configs/general_interface_FPT_config .config;

make olddefconfig
make -j `nproc` LOCALVERSION=-gen-FPT-L4L3L2L1