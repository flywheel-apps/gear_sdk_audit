#!/bin/bash

IFS=':'
read -ra paths <<< "$PATH"
for i in "${paths[@]}"; do
  ls -1 $i/pip*
done
