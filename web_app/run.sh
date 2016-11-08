#!/bin/bash

export VCAP_SERVICES=$(cat vcap.json)

python hello.py runserver -d
