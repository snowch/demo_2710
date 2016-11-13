import requests

from . import app

CL_URL      = app.config['CL_URL']
CL_AUTH     = app.config['CL_AUTH']
CL_MUSICDB  = app.config['CL_MUSICDB']
CL_AUTHDB   = app.config['CL_AUTHDB']
CL_RATINGDB = app.config['CL_RATINGDB']

# TODO use flask logging rather than print()
for db in [CL_MUSICDB, CL_AUTHDB, CL_RATINGDB]:
    response = requests.get( CL_URL+'/'+db, auth=CL_AUTH )

    if not response.status_code in [200, 201, 202]:

        print( 'Creating', db )
        response = requests.put( CL_URL+'/'+db, auth=CL_AUTH )

        if not response.status_code in [200, 201, 202]:
            print( 'Error creating ', db, response.text )
