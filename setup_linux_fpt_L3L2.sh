#!/bin/bash

git clone https://github.com/xlab-uiuc/emt-linux.git emt-linux-fpt-L3L2;
cd emt-linux-fpt-L3L2;
git checkout FPT;
cp configs/general_interface_FPT_config .config;

make olddefconfig
scripts/config --enable CONFIG_X86_64_FPT_L3L2
scripts/config --disable CONFIG_X86_64_FPT_L4L3L2L1
make -j `nproc` LOCALVERSION=-gen-FPT-L3L2