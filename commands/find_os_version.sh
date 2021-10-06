#!/bin/bash
#shopt -s extglob
cat /etc/os-release | grep PRETTY_NAME

# cat /etc/os-release | grep PRETTY_NAME | awk -F'"' '$0=$2' | awk '{print $1} {print $2}'
# lsb_release -a | grep "Description" | awk '{print $2} {print $3}'
