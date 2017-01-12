from datetime import datetime
import os, json
import requests
import urllib
from . import app
from app.cloudant_db import cloudant_client
from app.redis_db import get_next_user_id
from typing import List, Dict


RATINGDB_URL = app.config['CL_URL'] + '/' + app.config['CL_RATINGDB']

CL_URL      = app.config['CL_URL']
CL_MOVIEDB  = app.config['CL_MOVIEDB']
CL_AUTHDB   = app.config['CL_AUTHDB']
CL_RATINGDB = app.config['CL_RATINGDB']
CL_RECOMMENDDB = app.config['CL_RECOMMENDDB']

class DAO:

    @staticmethod
    def get_movie_names(movie_ids: List[int]) -> Dict[int, str]:
        """Retrieve the movie names from Cloudant.

        Args:
            movie_ids (List[int]): The movie ids to lookup the movie names for. 

        Returns:
            Dict[int, str]: Returns a dict with { movie_id: movie_name, ... }.
                            An empty dict will be returned if no movies are found for the ids.
        """

        # The movie_ids in cloudant are stored as strings so convert to correct format 
        # for querying
        movie_ids = [ str(id) for id in movie_ids ]

        keys = urllib.parse.quote_plus(json.dumps(movie_ids))

        # The movie id is stored in the _id field, so we query it using the 'keys' parameter
        end_point = '{0}/{1}/_all_docs?keys={2}&include_docs=true'.format ( 
                                                                CL_URL, CL_MOVIEDB, keys
                                                                )
        response = cloudant_client.r_session.get(end_point)
        movie_data = json.loads(response.text)

        movie_names = {}

        if 'rows' in movie_data:
            for row in movie_data['rows']:
                if 'doc' in row:
                    movie_id   = int(row['key'])
                    movie_name = row['doc']['name']

                    movie_names[movie_id] = movie_name

        return movie_names
