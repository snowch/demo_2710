#!/bin/bash

export FLASK_DEBUG=1
export VCAP_SERVICES="{$(cat cloudant_vcap.json),$(cat redis_vcap.json),$(cat messagehub_vcap.json)}"

if [ $# -eq 0 ]
then
    python manage.py runserver -d
fi

python manage.py "$@"
