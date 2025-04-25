#  EMT: An OS Framework for New Memory Translation Architectures

## Abstract
With terabyte-scale memory capacity and memory-intensive workloads, memory translation has become a major performance bottleneck. Many novel hardware schemes are developed to speed up memory translation, but few are experimented with commodity OSes. A main reason is that memory management in major OSes, like Linux, does not have the extensibility to empower emerging hardware schemes.

We develop EMT, a pragmatic framework atop Linux to em- power different hardware schemes of memory translation such as radix tree and hash table. EMT provides an architecture- neutral interface that 1) supports diverse memory translation architectures, 2) enables hardware-specific optimizations, 3) accommodates modern hardware and OS complexity, and 4) has negligible overhead over hardwired implementations. We port Linux’s memory management onto EMT and show that EMT enables extensibility without sacrificing performance. We use EMT to implement OS support for ECPT and FPT, two recent experimental translation schemes for fast translation; EMT enables us to understand the OS perspective of these architectures and further optimize their designs.


## Artifact Evaluation Guideline

### Repository overview
- *linux_emt*, Linux kernel implementation including support for x86-radix, ECPT, and FPT
- *qemu_emt*, QEMU emulation tool to test and evaluate architectures
- *dynamorio* Memory simulator for performance
- *rethinkVM_bench* benchmark repo for all benchmarks
