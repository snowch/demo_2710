#!/bin/bash

export FLASK_DEBUG=1
export VCAP_SERVICES="{$(cat etc/cloudant_vcap.json),$(cat etc/redis_vcap.json)}"

if [ $# -eq 0 ]
then
    python manage.py runserver -d
fi

python manage.py "$@"
