#!/bin/bash

git clone https://github.com/xlab-uiuc/emt-linux.git emt-linux-ecpt;
cd emt-linux-ecpt;
git checkout main;
cp configs/general_interface_ECPT_config .config;

make olddefconfig
make -j `nproc` LOCALVERSION=-gen-ECPT