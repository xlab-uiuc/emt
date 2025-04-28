#!/usr/bin/env bash

set -euo pipefail

# file locator
# SCRIPT_DIR=$(dirname "$(realpath -e "${BASH_SOURCE[0]:-$0}")")
# . "$SCRIPT_DIR/common.sh"

# Common
sudo apt-get update
sudo apt-get install -y apt-transport-https
sudo apt-get update
sudo apt-get install -y bash curl git man perl perl-doc sudo wget screen vim nano software-properties-common zip unzip tar rsync
sudo apt-get install -y python3 python3-dev python3-pip python3-venv python-is-python3
sudo apt install htop

# Kernel
sudo apt-get install -y build-essential linux-tools-common linux-tools-generic liblz4-tool dwarves binutils elfutils gdb flex bison libncurses-dev libssl-dev libelf-dev
sudo apt-get install -y cmake gcc g++ make libiberty-dev autoconf zstd libboost-all-dev arch-install-scripts
sudo apt-get install -y libdw-dev systemtap-sdt-dev libunwind-dev libslang2-dev libperl-dev liblzma-dev libzstd-dev libcap-dev libnuma-dev libbabeltrace-ctf-dev libbfd-dev
# sudo apt-get install -y clang clang-format clang-tools llvm

# Workloads
sudo apt-get install -y libreadline-dev

# Check we have everything we want
python3 --version
gcc --version
cmake --version 

sudo apt install -y cpu-checker hwloc
sudo apt install -y qemu-kvm virt-manager libvirt-daemon-system virtinst libvirt-clients bridge-utils

sudo apt install -y meson
sudo apt install -y libglib2.0-dev
sudo apt install -y pkg-config
sudo apt install -y libpixman-1-dev ripgrep
sudo apt install -y xz-utils

sudo apt install -y docker.io