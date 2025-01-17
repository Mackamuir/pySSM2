#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

cp ./logger.py /etc/pySSM2/logger.py
cp ./PySSM2.py /etc/pySSM2/PySSM2.py
cp -r ./static/ /etc/pySSM2/