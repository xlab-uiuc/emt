#!/bin/bash
git submodule init

# clone benchmark repo for instruction analysis
git submodule update --init --recursive VM-Bench

# clone dynamoRIO for performance analysis
git submodule update dynamorio
cd dynamorio
docker build -t dynamorio:latest .