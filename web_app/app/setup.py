import requests, json

from . import app

CL_URL      = app.config['CL_URL']
CL_AUTH     = app.config['CL_AUTH']
CL_MUSICDB  = app.config['CL_MUSICDB']
CL_AUTHDB   = app.config['CL_AUTHDB']
CL_RATINGDB = app.config['CL_RATINGDB']

def create_dbs():
    # TODO use flask logging rather than print()
    for db in [CL_MUSICDB, CL_AUTHDB, CL_RATINGDB]:
        response = requests.get( CL_URL+'/'+db, auth=CL_AUTH )

        if response.status_code in [200, 201, 202]:
            print( 'Found database {0}'.format(db) )
        else:

            print( 'Creating', db )
            response = requests.put( CL_URL+'/'+db, auth=CL_AUTH )

            if not response.status_code in [200, 201, 202]:
                print( 'Error creating ', db, response.text )

def create_musicdb_indexes():
    response = requests.get( CL_URL+'/'+CL_MUSICDB+'/_index', auth=CL_AUTH )
    
    if response.status_code in [200, 201, 202]:
    
        indexes = [ doc['name'] for doc in response.json()['indexes'] ]
    
        if 'title-artist-text' in indexes:
            print('Found {0} title-artist-text index'.format(CL_MUSICDB))
        else:
            idx = {
                "index": {
                    "fields": [
                        { "name": "title", "type": "string" },
                        { "name": "artist", "type": "string" }
                    ]
                },
                "name": "title-artist-text",
                "type": "text"
            }
            
            response = requests.post(
                    CL_URL+'/'+CL_MUSICDB+'/_index', 
                    auth=CL_AUTH, 
                    data=json.dumps(idx), 
                    headers={'Content-Type':'application/json'})
    
            if response.status_code in [200, 201, 202]:
                print('Created {0} title-artist-text index'.format(CL_MUSICDB))
            else:
                print('Issue encountered creating {0} title-artist-text index: {1}'.format(CL_MUSICDB, response.text))
    
create_dbs()
create_musicdb_indexes()
