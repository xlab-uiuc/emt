#!/bin/bash

git clone https://github.com/xlab-uiuc/qemu-emt.git qemu-fpt;
cd qemu-fpt;
git checkout execlog_addr_dump;

./configure_fpt_execlog.sh
make -j `nproc`