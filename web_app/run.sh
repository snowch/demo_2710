#!/bin/bash

export VCAP_SERVICES=$(cat vcap.json)

python manage.py runserver -d
