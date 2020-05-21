#!/bin/bash
shopt -s extglob
IFS=':'
read -ra paths <<< "$PATH"
for i in "${paths[@]}"; do
  #ls -1 $i/pip* 2> /dev/null | grep -E pip[0-9]?.?[0-9]?$
  ls -1 ${i}/${1} 2> /dev/null
done
