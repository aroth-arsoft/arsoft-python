#!/bin/sh
script_file=`readlink -f "$0"`
script_dir=`dirname "$script_file"`

docker build -t rothan/arsoft-python:latest "$script_dir"

docker push rothan/arsoft-python:latest
