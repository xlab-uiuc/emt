#  EMT: An OS Framework for New Memory Translation Architectures

## Abstract
With terabyte-scale memory capacity and memory-intensive workloads, memory translation has become a major performance bottleneck. Many novel hardware schemes are developed to speed up memory translation, but few are experimented with commodity OSes. A main reason is that memory management in major OSes, like Linux, does not have the extensibility to empower emerging hardware schemes.

We develop EMT, a pragmatic framework atop Linux to em- power different hardware schemes of memory translation such as radix tree and hash table. EMT provides an architecture- neutral interface that 1) supports diverse memory translation architectures, 2) enables hardware-specific optimizations, 3) accommodates modern hardware and OS complexity, and 4) has negligible overhead over hardwired implementations. We port Linux’s memory management onto EMT and show that EMT enables extensibility without sacrificing performance. We use EMT to implement OS support for ECPT and FPT, two recent experimental translation schemes for fast translation; EMT enables us to understand the OS perspective of these architectures and further optimize their designs.


## Artifact Evaluation Guideline

Note that we only apply for available and functional badge.
### Repository overview
- *linux_emt*, Linux kernel implementation including support for x86-radix, ECPT, and FPT
- *qemu_emt*, QEMU emulation tool to test and evaluate architectures
- *dynamorio* Memory simulator for performance
- *rethinkVM_bench* benchmark repo for all benchmarks


## Dependency Installation

```bash
git clone 2

./install_dependency.sh
```


## Radix Setup

#### QEMU Setup
Clone repo 
```bash
git clone https://github.com/xlab-uiuc/qemu_emt.git qemu_x86;
cd qemu_x86;
git checkout execlog_addr_dump;
```

Configure for radix and run
```bash
# Configure QEMU for x86 radix emulation with plugin support
./configure_radix_execlog.sh
make -j `nproc`
```

The compiled binary is at `build/qemu-system-x86_64`. 

#### Linux Setup
Clone linux repo and qemu repo under the **same** folder.
```bash
# get out of QEMU repo
cd ..;

git clone https://github.com/xlab-uiuc/linux_emt.git linux_gen_x86;
cd linux_gen_x86;
git checkout main;
cp configs/general_interface_radix_config .config;
```

Next, we compile the kernel.
```
make olddefconfig
make -j `nproc` LOCALVERSION=-gen-x86
```

#### Filesystem

To run linux with QEMU, you need a filesystem image.
We prepared a image that contains precompiled benchmark suites (from rethinkVM_bench).
We have already uploaded image to `/proj/AE25-PG0/EMT-images/image_record_loading.ext4.xz`.

Run the following commands to copy and decoompress.

```bash
# get out of Linux repo
cd ..;

# copy and decompress the image.
cp/proj/AE25-PG0/EMT-images/image_record_loading.ext4.xz .
unxz image_record_loading.ext4.xz
```

#### Simulator Preparation

```bash
# clone benchmark repo for instruction analysis
git clone https://github.com/xlab-uiuc/rethinkVM_bench.git

# clone dynamoRIO for performance analysis
git clone https://github.com/xlab-uiuc/dynamorio.git
```

#### Time to run

Run a graphbig benchmark with EMT-Linux and generate analysis file.
The output include instruction and memory trace which can be up to 150GB.
We will compress the trace to save space in the scripts.
Please select a disk drive with at least 200GB free space. 

Note that the script assuems image is located `../image_record_loading.ext4`
Please change the `IMAGE_PATH_PREFIX` in `./run_bench.sh` accordingly, if you have renamed it.
```bash
cd linux_gen_x86

# dry run to print the command to execute.
# Double check architecture, thp config, image path, output directory 
./run_bench.sh --arch radix --thp never --out benchmark_output --dry

# real run
./run_bench.sh --arch radix --thp never --out benchmark_output
```

The script will run and generate analysis files in `benchmark_output/radix/running`.
You can find a file with suffix `kern_inst.folded.high_level.csv` that contains kernel instruction distribution.
File ended with `bin.dyna_asplos_smalltlb_config_realpwc.log` is simulator result from DynamoRIO; the final simulation result can be found at the file ended with `dyna_asplos_smalltlb_config_realpwc.log.ipc.csv`


## ECPT setup

#### QEMU Setup
Clone QEMU and configure ECPT
```bash
# get out of linux_gen_x86 repo
cd ..; 
git clone https://github.com/xlab-uiuc/qemu_emt.git qemu_ECPT;
cd qemu_ECPT;
git checkout execlog_addr_dump;

./configure_ECPT_execlog.sh
make -j `nproc`
```

The compiled binary is still at `build/qemu-system-x86_64`. 
The name `qemu-system-x86_64` might be confusing here, 
but we have changed the implementation of QEMU's x86_64 to support ECPT,
so you are actually configure to compile x86_64 but with ECPT as address translation method. 


#### Linux Setup
Clone linux_gen_ECPT repo and qemu_ECPT repo under the **same** folder.
```bash
# get out of QEMU repo  
cd ..;

git clone https://github.com/xlab-uiuc/linux_emt.git linux_gen_ECPT;
cd linux_gen_ECPT;
git checkout main;
cp configs/general_interface_ECPT_config .config;

make olddefconfig
make -j `nproc` LOCALVERSION=-gen-ECPT
```

`general_interface_ECPT_config` configures linux to run on ECPT.

#### Time to run
Again, we need a filesystem to run.
We can reuse the image from last section.

```bash
# dry run to print the command to execute.
# Double check architecture, thp config, image path, output directory 
./run_bench.sh --arch ecpt --thp never --out benchmark_output --dry

# real run
./run_bench.sh --arch ecpt --thp never --out benchmark_output
```

You can find similar files in `benchmark_output/ecpt/running`.

## FPT setup

#### QEMU Setup
Clone QEMU and configure ECPT
```bash
# get out of linux_gen_x86 repo
cd ..; 
git clone https://github.com/xlab-uiuc/qemu_emt.git qemu_FPT;
cd qemu_FPT;
git checkout execlog_addr_dump;

./configure_fpt_execlog.sh
make -j `nproc`
```

#### Linux Setup
Clone linux_gen_FPT repo and qemu_FPT repo under the **same** folder.
```bash
# get out of QEMU repo  
cd ..;

git clone https://github.com/xlab-uiuc/linux_emt.git linux_gen_FPT;
cd linux_gen_FPT;
git checkout FPT;
cp configs/general_interface_FPT_config .config;

make olddefconfig
make -j `nproc` LOCALVERSION=-gen-FPT
```

#### Time to run

```bash
# dry run to print the command to execute.
# Double check architecture, thp config, image path, output directory 
./run_bench.sh --arch fpt --flavor L4L3_L2L1 --thp never --out benchmark_output --dry

# real run
./run_bench.sh --arch fpt --flavor L4L3_L2L1 --thp never --out benchmark_output
```

By default FPT runs with L4L3 and L2L1 flatenned. If you wish to try L3L2 folding.
```bash
scripts/config --enable CONFIG_X86_64_FPT_L3L2
scripts/config --disable CONFIG_X86_64_FPT_L4L3L2L1

make -j `nproc` LOCALVERSION=-gen-FPT
```

Then run benchmark with 
```bash
# real run
./run_bench.sh --arch fpt --flavor L3L2 --thp never --out benchmark_output
```