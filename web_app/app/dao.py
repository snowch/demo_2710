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
from cloudant.database import CloudantDatabase

CL_URL = app.config['CL_URL']

CL_MOVIEDB  = app.config['CL_MOVIEDB']
CL_AUTHDB   = app.config['CL_AUTHDB']
CL_RATINGDB = app.config['CL_RATINGDB']
CL_RECOMMENDDB = app.config['CL_RECOMMENDDB']

class RecommendationsNotGeneratedException(Exception):
    pass

class RecommendationsNotGeneratedForUserException(Exception):
    pass

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

        db = cloudant_client[CL_MOVIEDB]
        args = {
            "keys"         : movie_ids,
            "include_docs" : True
        }

        movie_data = db.all_docs(**args)
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
        args = {
            "startkey"     : 'user_{0}'.format(user_id),
            "endkey"       : 'user_{0}/ufff0'.format(user_id),
            "include_docs" : True
        }

        user_ratings = db.all_docs(**args)

        ratings = {}
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
        
        db = cloudant_client[CL_RATINGDB]

        current_milli_time = lambda: int(round(time.time() * 1000))

        id = 'user_{0}/movie_{1}'.format(user_id, movie_id)

        with Document(db, id) as document:
            if rating:
                document.update( { 'rating': rating, 'timestamp': current_milli_time() })
                print('saved/updated rating', id)
            else:
                if document.exists():
                    document.update( { '_deleted': True } )
                    print('deleted rating', id)


class RecommendationDAO:

    @staticmethod
    def get_latest_recommendation_timestamp() -> datetime:
        """Get the timestamp that the latest recommendations were generated

        Returns:
            datetime: Returns the UTC timestamp
        """

        db = cloudant_client[CL_RECOMMENDDB]

        # get recommendation_metadata document with last run details
        try:
            doc = db['recommendation_metadata']
            doc.fetch()
          
        except KeyError:
            print('recommendation_metadata doc not found in', CL_RECOMMENDDB)
            raise RecommendationsNotGeneratedException

        timestamp_str = doc['timestamp_utc']

        import dateutil.parser
        return dateutil.parser.parse(timestamp_str)
   
class UserDAO:

    @staticmethod
    def load_user(user_id: str) -> Dict[str, str]:
        """Load user details

        Args:
            user_ids  (str): The user id to load

        Returns:
            Dict[str, str]: Returns the user dict with the following fields:
                            {
                                'email': str
                                'password_hash': str
                            }
        """

        db = cloudant_client[CL_AUTHDB]

        user_dict = {}
        try:
            doc = db[user_id]
            doc.fetch()

            if doc.exists():
                user_dict['email'] = doc['email']
                user_dict['password_hash'] = doc['password_hash']
            
        except KeyError:
            pass

        return user_dict

    @staticmethod
    def find_by_email(email: str) -> Dict[str, str]:
        """Load user details

        Args:
            email (str): The user email address

        Returns:
            Dict[str, str]: Returns the user dict with the following fields:
                            {
                                'user_id': str
                                'password_hash': str
                            }
        """

        # FIXME - convert this to python-cloudant api

        auth_db = cloudant_client[CL_AUTHDB]
        key = urllib.parse.quote_plus(email)
        view_name = 'authdb-email-index'

        template = '{0}/{1}/_design/{2}/_view/{2}?key="{3}"&include_docs=true'
        endpoint = template.format ( 
                            CL_URL, 
                            CL_AUTHDB,
                            view_name,
                            key 
                            )

        response = cloudant_client.r_session.get(endpoint)

        user_dict = {}

        if response.status_code == 200:
            rows = response.json()['rows']
            if len(rows) > 0:
                user_dict['password_hash'] = rows[0]['doc']['password_hash']
                user_dict['user_id']       = rows[0]['doc']['_id']
                print("User found for email",  email)
            else:
                print("User not found for email", email)
                
        return user_dict

    @staticmethod
    def create_user(email: str, password_hash: str) -> int:
        """Create new user

        Args:
            email         (str): The user's email address
            password_hash (str): The user's password_hash

        Returns:
            int: The generated user id for the new user
        """

        db = cloudant_client[CL_AUTHDB]

        # Spark ALS requires user id's to be integers, and because
        # Cloudant does not have atomic incrementing integer fields,
        # we use Redis

        from app.redis_db import get_next_user_id
        id = get_next_user_id()

        data = { 
            "_id"           : str(id),
            "email"         : email,
            "password_hash" : password_hash
        }
        doc = db.create_document(data)

        if not doc.exists():
            raise BaseException("Coud not save user: " + data)

