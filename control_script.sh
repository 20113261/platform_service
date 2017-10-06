#!/usr/bin/env bash

# update supervisor info
cat hosts.txt|xargs -I host scp supervisord.conf host:/etc

# get free memory
pssh -h hosts.txt -i 'cat /proc/meminfo |grep MemFree'