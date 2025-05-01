#!/bin/bash

git clone https://github.com/xlab-uiuc/qemu-emt.git qemu-radix;
cd qemu-radix;
git checkout execlog_addr_dump;

# Configure QEMU for x86 radix emulation with plugin support
./configure_radix_execlog.sh
make -j `nproc`