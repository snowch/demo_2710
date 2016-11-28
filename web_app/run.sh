#!/bin/bash

export VCAP_SERVICES=$(cat vcap.json)

if [ $# -eq 0 ]
then
    python manage.py runserver -d
fi

python manage.py "$@"
