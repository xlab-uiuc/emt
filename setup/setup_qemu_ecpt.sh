#!/bin/bash

git clone https://github.com/xlab-uiuc/qemu-emt.git qemu-ecpt;
cd qemu-ecpt;
git checkout execlog_addr_dump;

./configure_ECPT_execlog.sh
make -j `nproc`