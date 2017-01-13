from datetime import datetime
import time
import os, json
import requests
import urllib
from . import app
from app.cloudant_db import cloudant_client
from app.redis_db import get_next_user_id
from typing import List, Dict, Optional
from cloudant.document import Document


RATINGDB_URL = app.config['CL_URL'] + '/' + app.config['CL_RATINGDB']

CL_URL      = app.config['CL_URL']
CL_MOVIEDB  = app.config['CL_MOVIEDB']
CL_AUTHDB   = app.config['CL_AUTHDB']
CL_RATINGDB = app.config['CL_RATINGDB']
CL_RECOMMENDDB = app.config['CL_RECOMMENDDB']

class MovieDAO:

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

class RatingDAO:

    @staticmethod
    def get_ratings(user_id: int) -> Dict[int, float]:
        """Retrieve user's rated movies.

        Args:
            user_id (int): The user_id whose movie ratings you require. 

        Returns:
            Dict[int, float]: Returns a dict with { movie_id: rating, ... }.
                              An empty dict will be returned if no movies have been rated
                              by the user.
        """

        db = cloudant_client[CL_RATINGDB]

        # The rating document _id format is: user_n/movie_n

        end_point = "{0}/{1}/_all_docs?" + \
                    "start_key=%22user_{2}%22&end_key=%22user_{2}%2Fufff0%22&" + \
                    "include_docs=true".format( 
                                            CL_URL, CL_RATINGDB, user_id 
                                            )

        headers = { "Content-Type": "application/json" }
        response = cloudant_client.r_session.get(end_point, headers=headers)

        ratings = {}

        user_ratings = json.loads(response.text)
        if 'rows' in user_ratings:
            for row in user_ratings['rows']:
                movie_id = int(row['doc']['_id'].split('/')[1].split('_')[1])
                rating = float(row['doc']['rating'])

                ratings[movie_id] = rating

        return ratings

    @staticmethod
    def save_rating(movie_id: int, user_id: int, rating: Optional[float]):
        """Save user's rated movie

        Args:
            movie_ids (int):             The movie id that was rated
            user_ids  (int):             The user id rating the movie
            rating    (Optional[float]): The movie rating

        If the rating argument is not None:
           - If the rating doesn't exist in the database it will be created
           - If the rating does exist in the database it will be updated 

        If the rating argument is None:
           - If the rating doesn't exist in the database no operation will be performed 
           - If the rating does exist in the database it will be deleted
        """
        
        current_milli_time = lambda: int(round(time.time() * 1000))

        db = cloudant_client[CL_RATINGDB]

        id = 'user_{0}/movie_{1}'.format(user_id, movie_id)

        with Document(db, id) as document:
            if rating:
                document.update( { 'rating': rating, 'timestamp': current_milli_time() })
                print('saved/updated rating', id)
            else:
                if document.exists():
                    document.update( { '_deleted': True } )
                    print('deleted rating', id)

