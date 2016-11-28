import requests, json

from app import app
from app.cloudant_db import cloudant_client
from cloudant.design_document import DesignDocument
from requests.exceptions import HTTPError

CL_URL      = app.config['CL_URL']
CL_AUTH     = app.config['CL_AUTH']
CL_MOVIEDB  = app.config['CL_MOVIEDB']
CL_AUTHDB   = app.config['CL_AUTHDB']
CL_RATINGDB = app.config['CL_RATINGDB']

CL_DBS = [ CL_MOVIEDB, CL_AUTHDB, CL_RATINGDB ]


# TODO use flask logging rather than print()

def delete_dbs():

    dbs = cloudant_client.all_dbs()
    for db in CL_DBS:
        if db in dbs:
            print('Deleting database', db)
            cloudant_client.delete_database(db)

def create_dbs():

    dbs = cloudant_client.all_dbs()
    for db in CL_DBS:
        if db in dbs:
            print('Found database', db)
        else:
            db_handle = cloudant_client.create_database(db)
            if db_handle.exists():
                print('Created database', db)
            else:
                print('Problem creating database', db)

def md5(fname):
    import hashlib
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_movie_data():
    zip_filename = 'ml-1m.zip'

    import os.path
    if os.path.isfile(zip_filename) and md5(zip_filename) == 'c4d9eecfca2ab87c1945afe126590906':
        print("Skipping download of ml-1m.zip as it already exists") 
    else:
        print("Downloading ml-1m.zip")
        import urllib.request
        url = 'http://files.grouplens.org/datasets/movielens/ml-1m.zip'
        urllib.request.urlretrieve(url, zip_filename)

    import zipfile
    with zipfile.ZipFile(zip_filename,"r") as zip_ref:
        zip_ref.extractall()

def populate_movie_db():
    download_movie_data()

    movie_file = 'ml-1m/movies.dat'

    with open(movie_file, 'r', encoding='ISO-8859-1') as f:
        for line in f:
            (movieid, moviename, category) = line.strip().split('::')

            data = {
                '_id': movieid,
                'name': moviename,
                'categories': [category.split('|')]
                }
            movie_db = cloudant_client[CL_MOVIEDB]
            my_document = movie_db.create_document(data)
            if my_document.exists():
                print("Created movieid: ", movieid)
            else:
                print("Couldn't create movieid: ", movieid)


def create_moviedb_indexes():

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
    musicdb = cloudant_client[CL_MOVIEDB]
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
