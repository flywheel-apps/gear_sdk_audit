#!/bin/bash
shopt -s extglob
#echo $PATH
IFS=':'
read -ra paths <<< "$PATH"
for i in "${paths[@]}"; do
  #ls -1 $i/pip* 2> /dev/null | grep -E pip[0-9]?.?[0-9]?$
  a=`command -v realpath`
  if [ ! -z $a ]; then
    
    for p in ${i}/${1}; do
      #echo "1:$p"
      echo `realpath $p`
    done
    
  else
    ls -1 ${i}/${1} 2> /dev/null
  fi
  
done
