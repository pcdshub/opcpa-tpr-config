#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo
    echo "Incorrect number of parameters"
    echo "Usage: $0 <pv1> <val1> <pv2> <val2>"
    echo
    exit 2
fi

PV1=$1
VAL1=$2
PV2=$3
VAL2=$4

echo
echo Setting $PV1 to $VAL1
echo Setting $PV2 to $VAL2
echo
