#!/bin/bash
set -e
outfile=./date.staticx

echo -e "\n\nTest StaticX against 'date'"

cd "$(dirname "${BASH_SOURCE[0]}")"


echo -e "\nRunning 'date':"
date

echo -e "\nMaking staticx executable:"
staticx $(which date) $outfile

echo -e "\nRunning staticx executable"
$outfile

echo -e "\nRunning staticx executable under CentOS 5"
scuba --image centos:5 $outfile
