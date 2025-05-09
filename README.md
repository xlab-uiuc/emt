#  EMT: An OS Framework for New Memory Translation Architectures

## Abstract
With terabyte-scale memory capacity and memory-intensive workloads, memory translation has become a major performance bottleneck. Many novel hardware schemes are developed to speed up memory translation, but few are experimented with commodity OSes. A main reason is that memory management in major OSes, like Linux, does not have the extensibility to empower emerging hardware schemes.

We develop EMT, a pragmatic framework atop Linux to em- power different hardware schemes of memory translation such as radix tree and hash table. EMT provides an architecture- neutral interface that 1) supports diverse memory translation architectures, 2) enables hardware-specific optimizations, 3) accommodates modern hardware and OS complexity, and 4) has negligible overhead over hardwired implementations. We port Linux’s memory management onto EMT and show that EMT enables extensibility without sacrificing performance. We use EMT to implement OS support for ECPT and FPT, two recent experimental translation schemes for fast translation; EMT enables us to understand the OS perspective of these architectures and further optimize their designs.


## Artifact Evaluation Guideline

<!-- Note that we only apply for available and functional badge. -->
### Repository overview
- *emt-linux*, Linux kernel implementation including support for x86-radix, ECPT, and FPT
- *qemu-emt*, QEMU emulation tool to test and evaluate architectures
- *dynamorio* Memory simulator for performance
- *VM-Bench* benchmark repo for all benchmarks
- *collect_data.sh* one click script to collect simulation data.
- *analyze_data.sh* one click script to generate plots. It uses `ecpt_unified.py` `ipc_with_inst.py` and `kern-inst-breakdown-with-khuge-unified.py`.

## Machine Requirements

- Simulation experiment: We reserved machines on cloudlab. You can join the project `AE25` and find experiment `OSDI2025-EMT-AE`. 
- Baremetal experiment: To avoid complexity of handling kernel installation on baremetal machines, we provide a machine with kernel installed and setup environments for you. Please refer to the hotcrp page for information on how to access it.

## Simulation Setup and Minimal Working Example

### Dependency Installation

The following instructions are tested on Ubuntu 22.04 environment.

```bash
git clone https://github.com/xlab-uiuc/EMT-OSDI-AE.git
cd EMT-OSDI-AE
./setup/install_dependency.sh
```

**PS**: `./setup/install_dependency.sh` installs necessary packages for compilation and docker environment. Please relogin or run.
```
newgrp docker
```
to make docker group active.


### Radix Setup

#### QEMU Setup
<!-- Clone repo  -->

```bash
# Clone QEMU repo and build QEMU with x86-radix softmmu
./setup/setup_qemu_radix.sh
```

<!-- ```bash
git clone https://github.com/xlab-uiuc/qemu-emt.git qemu-radix;
cd qemu-radix;
git checkout execlog_addr_dump;
```

Configure for radix and run
```bash
# Configure QEMU for x86 radix emulation with plugin support
./configure_radix_execlog.sh
make -j `nproc`
``` -->

The compiled binary is at `qemu-radix/build/qemu-system-x86_64`. 

#### Linux Setup

```bash
# Clone Linux repo and build EMT-Linux with x86-radix MMU driver
./setup/setup_linux_radix.sh
```
You can find linux folder at `emt-linux-radix`.

<!-- Clone linux repo and qemu repo under the **same** folder.
```bash
# get out of QEMU repo
cd ..;

git clone https://github.com/xlab-uiuc/emt-linux.git emt-linux-radix;
cd emt-linux-radix;
git checkout main;
cp configs/general_interface_radix_config .config;
```

Next, we compile the kernel.
```
make olddefconfig
make -j `nproc` LOCALVERSION=-gen-x86
``` -->

#### Filesystem

To run linux with QEMU, you need a filesystem image.
We prepared a image that contains precompiled benchmark suites (from VM-Bench).
We have already uploaded image to `/proj/ae25-PG0/EMT-images/image_record_loading.ext4.xz`.

Run the following commands to copy and decoompress. (Please make sure we are still in the `EMT-OSDI-AE` root folder.)

```bash
# copy and decompress the image.
cp /proj/ae25-PG0/EMT-images/image_record_loading.ext4.xz .
unxz image_record_loading.ext4.xz
```

#### Simulator Preparation

The script will setup `dynamorio` and `VM-Bench` repo.
They contain simulator and instruction trace analyzer.
```bash
./setup/setup_simulator.sh
```


<!-- ```bash
git submodule init

# clone benchmark repo for instruction analysis
git submodule update --init --recursive VM-Bench

# clone dynamoRIO for performance analysis
git submodule update dynamorio
cd dynamorio
docker build -t dynamorio:latest .
cd ..
``` -->

#### Time to run [Est. time 2 hours]

Run a graphbig benchmark with EMT-Linux and generate analysis file.
The output include instruction and memory trace which can be up to 150GB.
The script will compress the trace to save space in the end.
Please select a disk drive with at least 200GB free space.

*Note* If you are on a cloudlab machine, the home directory will likely not have enough space to finish the workload.
We provide a [guide](guides/disk.md) to mount an extra disk under directory `/data/EMT`

Note that the script assuems image is located `../image_record_loading.ext4`
Please change the `IMAGE_PATH_PREFIX` in `./run_bench.sh` accordingly, if you have renamed the image.
```bash
cd emt-linux-radix

# dry run to print the command to execute.
# Double check architecture, thp config, image path, output directory 
./run_bench.sh --arch radix --thp never --out /data/EMT --dry

# real run
./run_bench.sh --arch radix --thp never --out /data/EMT
```

The script will run and generate analysis files in `/data/EMT/radix/running`.
You can find a file with suffix `kern_inst.folded.high_level.csv` that contains kernel instruction distribution.
File ended with `bin.dyna_asplos_smalltlb_config_realpwc.log` is simulator result from DynamoRIO; the final simulation result can be found at the file ended with `dyna_asplos_smalltlb_config_realpwc.log.ipc.csv`


### ECPT setup

Note that if you just ended running command above, please return back to the root folder (`EMT-OSDI-AE`).

#### QEMU Setup
<!-- Clone QEMU and configure ECPT
```bash
# get out of emt-linux-radix repo
cd ..; 
git clone https://github.com/xlab-uiuc/qemu-emt.git qemu-ecpt;
cd qemu-ecpt;
git checkout execlog_addr_dump;

./configure_ECPT_execlog.sh
make -j `nproc`
``` -->

```bash
# Clone QEMU repo and build with ECPT softmmu support
./setup/setup_qemu_ecpt.sh
```
The compiled binary is still at `qemu-ecpt/build/qemu-system-x86_64`. 
The name `qemu-system-x86_64` might be confusing here, 
but we have changed the implementation of QEMU's x86_64 to support ECPT,
so you are actually configure to compile x86_64 but with ECPT as address translation method. 


#### Linux Setup
<!-- Clone emt-linux-ecpt repo and qemu-ecpt repo under the **same** folder. -->
The script will setup linux directory at `emt-linux-ecpt`.
```bash
# Clone Linux repo and build EMT-Linux with ECPT MMU driver
./setup/setup_linux_ecpt.sh
```
<!-- ```bash
# get out of QEMU repo  
cd ..;

git clone https://github.com/xlab-uiuc/emt-linux.git emt-linux-ecpt;
cd emt-linux-ecpt;
git checkout main;
cp configs/general_interface_ECPT_config .config;

make olddefconfig
make -j `nproc` LOCALVERSION=-gen-ECPT
``` -->

<!-- `general_interface_ECPT_config` configures linux to run on ECPT. -->

#### Time to run [Est. time 2 hours]
Again, we need a filesystem to run.
We can reuse the image from last section.

```bash
cd emt-linux-ecpt

# dry run to print the command to execute.
# Double check architecture, thp config, image path, output directory 
./run_bench.sh --arch ecpt --thp never --out /data/EMT --dry

# real run
./run_bench.sh --arch ecpt --thp never --out /data/EMT
```

You can find similar files in `/data/EMT/ecpt/running`.

### FPT setup 

#### QEMU Setup
<!-- Clone QEMU and configure ECPT -->
<!-- ```bash
# get out of emt-linux-radix repo
cd ..; 
git clone https://github.com/xlab-uiuc/qemu-emt.git qemu-fpt;
cd qemu-fpt;
git checkout execlog_addr_dump;

./configure_fpt_execlog.sh
make -j `nproc`
``` -->

```bash
# Clone QEMU repo and build with FPT softmmu support
./setup/setup_qemu_fpt.sh
```
Output folder `qemu-fpt`.

#### Linux Setup

```bash
# Clone Linux repo and build EMT-Linux with FPT (L4L3 L2L1) MMU driver
./setup/setup_linux_fpt_L4L3L2L1.sh
```
Output folder `emt-linux-fpt-L4L3L2L1`.

<!-- Clone emt-linux-fpt repo and qemu-fpt repo under the **same** folder.
```bash
# get out of QEMU repo  
cd ..;

git clone https://github.com/xlab-uiuc/emt-linux.git emt-linux-fpt;
cd emt-linux-fpt;
git checkout FPT;
cp configs/general_interface_FPT_config .config;

make olddefconfig
make -j `nproc` LOCALVERSION=-gen-FPT
``` -->

#### Time to run [Est. time 2 hours]

```bash
cd emt-linux-fpt-L4L3L2L1
# dry run to print the command to execute.
# Double check architecture, thp config, image path, output directory 
./run_bench.sh --arch fpt --flavor L4L3_L2L1 --thp never --out /data/EMT --dry

# real run
./run_bench.sh --arch fpt --flavor L4L3_L2L1 --thp never --out /data/EMT
```

By default FPT runs with L4L3 and L2L1 flatenned. If you wish to try L3L2 folding.

```bash
# Clone Linux repo and build EMT-Linux with FPT (L4L3 L2L1) MMU driver
./setup/setup_linux_fpt_L3L2.sh
```
Output folder `emt-linux-fpt-L3L2`.


<!-- ```bash
scripts/config --enable CONFIG_X86_64_FPT_L3L2
scripts/config --disable CONFIG_X86_64_FPT_L4L3L2L1

make -j `nproc` LOCALVERSION=-gen-FPT
``` -->

Then run benchmark with 
```bash
# real run
cd emt-linux-fpt-L3L2;
./run_bench.sh --arch fpt --flavor L3L2 --thp never --out /data/EMT
```

## Procedures to Reproduce Fig 16 and Fig 20 (Appendix)

### Validation Claims

We aim to validate the following claims:
- EMT-ECPT will lead to more (> 1.2x) kernel overheads in both 4KB and THP setup.
- EMT-ECPT will have positive (> 1.0x) page walk latency speedup.
- EMT-ECPT will have positive (> 1.0x) IPC speedup.
- EMT-ECPT will positive but limited (> 1.0x but < 1.1x) total cycle reductions.


### Data Collection

Due to the long time to simulate all the benchmarks, 
we provide a script to run six representative benchmarks: `graphbig_bfs`, `graphbig_dfs`, `graphbig_dc`, `graphbig_sssp`, `gups`, and `redis`. 
It collects data for two archictures (radix/ECPT) at two THP configurations (4KB/THP) and two application stages (running/loading)

> Note (MUST READ): 
> 1. The following experiment will take about 3 - 4 days to finish, please run it ahead of time. 
> 2. Please run with tmux to avoid the script from being killed.
> 3. Please make sure `/data` is mounted with at least 500GB space.
One click run:
```
# Usage: ./collect_data.sh [--dry] [--out <destination>]

./collect_data.sh
```

You can use `--dry` flag to see the commands without executing them; you can also use `--out` to specify a custom directory to store the data.

By default, benchmarks are executed sequentially. 
If your system has sufficient CPU, memory, and storage resources, you may modify the script to introduce parallelism for faster data collection.

### Data Analysis

We provide a script to analyze the collected benchmark data.

```
# Usage: ./analyze_data.sh [--dry] [--thp never|always|all] [--input <source directory>] [--ipc_stats <pos>] [--inst_stats <pos>] [--graph <pos>]

./analyze_data.sh
```

Optional flags:
- `--dry` Print the commands that would be executed without actually running them.
- `--thp` Specify which THP configuration(s) to analyze. Use `all` to process both.
- `--input` Set the root directory containing raw benchmark results (default:`/data/EMT`).
- `--ipc_stats` Customize the output directory for IPC statistics (default: `./ipc_stats`).
- `--inst_stats` Customize the output directory for instruction statistics (default: `./inst_stats`).
- `--graph` Set the destination folder for all generated plots (default: `./graph`).



This script will generate statistics of the benchmarks, in `csv` format, and generate visualizations for them. 
You can find the plots under `./graph` directory.
- `./graph/kern_inst_unified_never.pdf` corresponds to Figure 16 a)
- `./graph/kern_inst_unified_always.pdf` corresponds to Figure 16 a)
- `./graph/ecpt_pgwalk_never.svg` corresponds to Figure 20 a)
- `./graph/ecpt_ipc_never.svg` corresponds to Figure 20 b)
- `./graph/ecpt_e2e_never.svg` corresponds to Figure 20 c)


## Procedures to Reproduce Fig 14 and Fig 15

### Validation Claims
We aim to validate the following claims:
- Compared to vanilla Linux, EMT-Linux with radix MMU driver introduces little (< 5%) overheads.


### Data Collection

The following script will run macro benchmarks and real world applications.
Due to the time it takes to rerun all kernel micro benchmarks, we put that as a optional part of the evulation.
Let us know if you need further instructions on that.

We give an estimate of how long each benchmarks will take.
- Macrobenchmarks, 40 mins
- Redis, 1 hour 20 mins
- Postgres, 1 hour 30 mins
- Memcached, 6 hours 30 mins

```bash
# on CSL machine with vanilla Linux

# Create a tmux session
cd /disk/ssd1/OSDI2025AE/VM-Bench/
./run_all.sh

# Ask the author to reboot to EMT-Linux 

# Create a tmux session
cd /disk/ssd1/OSDI2025AE/VM-Bench/
./run_all.sh
```
### Data Analysis

```bash
# on whichever kernel
cd /disk/ssd1/OSDI2025AE/VM-Bench/
./plot_baremetal.sh
```
You can find the plots under `./ae_results/${USER}` directory.
- `./ae_results/${USER}/radix.pdf` corresponds to Figure 14 b)
- `./ae_results/${USER}/radix_real_app_throughput.pdf` corresponds to Figure 15 a)
- `./ae_results/${USER}/radix_real_app_avg_latency.pdf` corresponds to Figure 15 b)
- `./ae_results/${USER}/radix_real_app_p99_latency.pdf` corresponds to Figure 15 c)




