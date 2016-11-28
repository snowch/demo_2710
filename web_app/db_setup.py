import requests, json

from app import app
from app.cloudant_db import cloudant_client
from cloudant.design_document import DesignDocument
from requests.exceptions import HTTPError

CL_URL      = app.config['CL_URL']
CL_AUTH     = app.config['CL_AUTH']
CL_MUSICDB  = app.config['CL_MUSICDB']
CL_AUTHDB   = app.config['CL_AUTHDB']
CL_RATINGDB = app.config['CL_RATINGDB']

# http://files.grouplens.org/datasets/movielens/ml-1m.zip

# TODO use flask logging rather than print()

def delete_dbs():

    dbs = cloudant_client.all_dbs()

    for db in [CL_MUSICDB, CL_AUTHDB, CL_RATINGDB]:

        if db in dbs:
            print('Deleting database', db)
            cloudant_client.delete_database(db)

def create_dbs():

    dbs = cloudant_client.all_dbs()

    for db in [CL_MUSICDB, CL_AUTHDB, CL_RATINGDB]:

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

    ddoc_fn = '''
function(doc){
  index("default", doc._id);
  if (doc.artist){
    index("artist", doc.artist, {"store": true});
  }
  if (doc.title){
    index("title", doc.title, {"store": true});
  }
}
'''    
    musicdb = cloudant_client[CL_MUSICDB]
    ddoc = DesignDocument(musicdb, 'artist-title-index')

    try:
        ddoc.fetch()
        ddoc.update_search_index('artist-title-index', ddoc_fn, analyzer=None)
    except HTTPError:
        print('httperror fetching {0} design doc', 'artist-title-index')
        ddoc.add_search_index('artist-title-index', ddoc_fn, analyzer=None)

    ddoc.save()

    
#create_dbs()
#create_musicdb_indexes()
#create_ratingdb_indexes()
