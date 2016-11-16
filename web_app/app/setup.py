import requests, json

from . import app
from .cloudant_db import cloudant_client

CL_URL      = app.config['CL_URL']
CL_AUTH     = app.config['CL_AUTH']
CL_MUSICDB  = app.config['CL_MUSICDB']
CL_AUTHDB   = app.config['CL_AUTHDB']
CL_RATINGDB = app.config['CL_RATINGDB']

def create_dbs():

    dbs = cloudant_client.all_dbs()

    # TODO use flask logging rather than print()
    for db in [CL_MUSICDB, CL_AUTHDB, CL_RATINGDB]:
        response = requests.get( CL_URL+'/'+db, auth=CL_AUTH )

        if db in dbs:
            print('Found database', db)
        else:
            db_handle = cloudant_client.create_database(db)

            if db_handle.exists():
                print('Created database', db)
            else:
                print('Problem creating database', db)
            

def create_test_ratingdb_doc():
    import random
    import time

    current_milli_time = lambda: int(round(time.time() * 1000))

    albums = ["bf129f0d", "380e3a05", "3d09ca05", "c912ae0d", "6b096208", "65120c09", "3709c305", "890b0b0b", "ae10d40d", "1212b314", "450a6205", "5d112207", "cc11060e", "3c0c3c05", "c70bc80f", "d40c110e", "520f7006", "c00ec30e", "3b0a6305", "4c081b06", "1b123324"]

    for num_ratings in [1, 2]:
        for album in albums:
            for user_id in [ 'a@a.com', 'a@b.com' ]:
                data = {
                    "album_id": album,
                    "user_id": user_id,
                    "rating": random.randint(1,5),
                    "timestamp": current_milli_time()
                }
                response = requests.post(
                        CL_URL+'/'+CL_RATINGDB, 
                        auth=CL_AUTH, 
                        data=json.dumps(data), 
                        headers={'Content-Type':'application/json'})



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
                        { "name": "title",  "type": "string" },
                        { "name": "artist", "type": "string" },
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

def create_ratingdb_indexes():
    response = requests.get( CL_URL+'/'+CL_RATINGDB+'/_index', auth=CL_AUTH )
    
    if response.status_code in [200, 201, 202]:
    
        indexes = [ doc['name'] for doc in response.json()['indexes'] ]
    
        if 'album-rating-text' in indexes:
            print('Found {0} album-rating-text index'.format(CL_RATINGDB))
        else:
            idx = {
                "index": {
                    "fields": [
                        { "name": "user_id",   "type": "string" },
                        { "name": "album_id",  "type": "string" },
                        { "name": "timestamp", "type": "number" }
                    ]
                },
                "name": "album-rating-text",
                "type": "text"
            }
            print(json.dumps(idx))
            response = requests.post(
                    CL_URL+'/'+CL_RATINGDB+'/_index', 
                    auth=CL_AUTH, 
                    data=json.dumps(idx), 
                    headers={'Content-Type':'application/json'})
    
            if response.status_code in [200, 201, 202]:
                print('Created {0} album-rating-text index'.format(CL_RATINGDB))
            else:
                print('Issue encountered creating {0} album-rating-text index: {1}'.format(CL_RATINGDB, response.text))

    
create_dbs()
create_musicdb_indexes()
create_ratingdb_indexes()
