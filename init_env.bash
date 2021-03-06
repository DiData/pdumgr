#!/bin/bash

if [ ! -d "env" ]; then
    virtualenv env
    source env/bin/activate
    pip install pysnmp regex python-nmap requests
else
    source env/bin/activate
fi
