import requests, json
import os.path

from app import app
from app.cloudant_db import cloudant_client
from app.redis_db import set_next_user_id

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

    movie_file = 'ml-1m/movies.dat'
    if not os.path.isfile(movie_file):
        download_movie_data()
    
    movie_db = cloudant_client[CL_MOVIEDB]

    bulk_docs = []
    with open(movie_file, 'r', encoding='ISO-8859-1') as f:
        for line in f:
            (movieid, moviename, category) = line.strip().split('::')

            bulk_docs.append({
                '_id': movieid,
                'name': moviename,
                'categories': [category.split('|')]
                })

    resp = movie_db.bulk_docs(bulk_docs)
    num_ok = len([ r['ok'] for r in resp if 'ok' in r ])
    print('num saved: ', num_ok)

def populate_rating_db():

    rating_file = 'ml-1m/ratings.dat'
    if not os.path.isfile(rating_file):
        download_movie_data()
    
    rating_db = cloudant_client[CL_RATINGDB]

    max_user_id = 0
    chunk = 0
    bulk_docs = []
    with open(rating_file, 'r', encoding='ISO-8859-1') as f:
        while True:
            line = f.readline().strip()

            if not line == '':
                (user_id, movie_id, rating, timestamp) = line.split('::')

                user_id = int(user_id)

                if user_id > max_user_id:
                    max_user_id = user_id
                
                bulk_docs.append({
                    'user_id': user_id,
                    'movie_id': movie_id,
                    'rating': rating,
                    'timestamp': timestamp
                    })
                chunk = chunk + 1

                # max request size is 1MB - we need to ensure chunks are 
                # smaller than this, 10000 docs was chosen arbitrarily and
                # seems to be ok

                if chunk % 10000 == 0:
                    resp = rating_db.bulk_docs(bulk_docs)
                    num_ok = len([ r['ok'] for r in resp if 'ok' in r ])
                    print('chunk: ', chunk, ' num saved: ', num_ok)
                    bulk_docs = []

                    # only load 10000 ratings for now
                    break
            else:
                break

    set_next_user_id(max_user_id + 1)


def create_moviedb_indexes():

    ddoc_fn = '''
function(doc){
  index("default", doc._id);
  if (doc.name){
    index("name", doc.name, {"store": true});
  }
}
'''    
    db = cloudant_client[CL_MOVIEDB]
    index_name = 'movie-search-index'

    ddoc = DesignDocument(db, index_name)
    if ddoc.exists():
        ddoc.fetch()
        ddoc.update_search_index(index_name, ddoc_fn, analyzer=None)
        print('updated', index_name)
    else:
        ddoc.add_search_index(index_name, ddoc_fn, analyzer=None)
        print('created', index_name)
    ddoc.save()

    # Test the index

    end_point = '{0}/{1}/_design/{2}/_search/{2}'.format ( CL_URL, CL_MOVIEDB, index_name )
    data = {
        "q": "name:Toy Story",
        "sort": "foo",
        "limit": 3
    }
    headers = { "Content-Type": "application/json" }
    response = cloudant_client.r_session.post(end_point, data=json.dumps(data), headers=headers)
    print(response.json())

def create_ratingdb_indexes():

    db = cloudant_client[CL_RATINGDB]

    ddoc_fn = '''
function(doc){
  if (doc.movie_id) {
    emit(doc.movie_id, doc.user_id);
  }
}
'''    
    view_name = 'rating-search-index'

    ddoc = DesignDocument(db, view_name)
    if ddoc.exists():
        ddoc.fetch()
        ddoc.update_view(view_name, ddoc_fn)
        print('updated', view_name)
    else:
        ddoc.add_view(view_name, ddoc_fn)
        print('created', view_name)
    ddoc.save()

    # Test the index

    end_point = '{0}/{1}/_design/{2}/_view/{2}'.format ( CL_URL, CL_RATINGDB, view_name )
    data = {
        "keys": "a@a.com",
    }
    # ?q=*:*&limit=1&group_field=division&include_docs=true&sort_field=-timestamp
    headers = { "Content-Type": "application/json" }
    response = cloudant_client.r_session.post(end_point, data=json.dumps(data), headers=headers)
    print(response.json())


def create_authdb_indexes():

    db = cloudant_client[CL_AUTHDB]

    ddoc_fn = '''
function(doc){
  if (doc.email) {
    emit(doc.email);
  }
}
'''    
    view_name = 'authdb-email-index'

    ddoc = DesignDocument(db, view_name)
    if ddoc.exists():
        ddoc.fetch()
        ddoc.update_view(view_name, ddoc_fn)
        print('updated', view_name)
    else:
        ddoc.add_view(view_name, ddoc_fn)
        print('created', view_name)
    ddoc.save()

    # Test the index

    import urllib
    key = urllib.parse.quote_plus('a@a.com')

    end_point = '{0}/{1}/_design/{2}/_view/{2}?key="{3}"'.format ( CL_URL, CL_AUTHDB, view_name, key )
    response = cloudant_client.r_session.get(end_point)
    print(response.json())
