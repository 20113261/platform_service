#!/usr/bin/env bash

# update supervisor info
cat hosts.txt|xargs -I host scp supervisord.conf host:/etc

# get free memory
pssh -h hosts.txt -i 'cat /proc/meminfo |grep MemFree'

# restart all running process
ps -aux|grep "celery worker"|grep -v grep|awk '{print $2}'|xargs -I each_pid kill -HUP each_pid

# get all running process pid
/usr/bin/pssh -h /root/hosts.txt -i "ps -aux|grep 'celery worker'|grep -v grep|awk '{print \$2}'"

# restart all running process from master
/usr/bin/pssh -h /root/hosts.txt -i "ps -aux|grep 'celery worker'|grep -v grep|awk '{print \$2}'|xargs -I each_pid kill -HUP each_pid"