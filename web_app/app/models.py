from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import g, current_app, request, url_for, jsonify
from flask.json import JSONEncoder
from flask.ext.login import UserMixin, AnonymousUserMixin, current_user
import os, json
import requests
import time
import urllib
from . import app, login_manager
from app.cloudant_db import cloudant_client
from app.redis_db import get_next_user_id
import collections
import numpy as np

current_milli_time = lambda: int(round(time.time() * 1000))

RATINGDB_URL = app.config['CL_URL'] + '/' + app.config['CL_RATINGDB']

CL_URL      = app.config['CL_URL']
CL_MOVIEDB  = app.config['CL_MOVIEDB']
CL_AUTHDB   = app.config['CL_AUTHDB']
CL_RATINGDB = app.config['CL_RATINGDB']
CL_RECOMMENDDB = app.config['CL_RECOMMENDDB']

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Movie):
            return obj.as_dict()
        if isinstance(obj, Recommendation):
            return obj.as_dict()
        else:
            JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder


class RecommendationsNotGeneratedException(Exception):
    pass

class RecommendationsNotGeneratedForUserException(Exception):
    pass

class Recommendation:

    def __init__(self, movie_id, movie_name, rating):
        self.movie_id = movie_id
        self.movie_name = movie_name
        self.rating = rating

    @staticmethod
    def get_latest_recommendation_timestamp():

        meta_db = cloudant_client[CL_RECOMMENDDB]

        # get recommendation_metadata document with last run details
        meta_doc = meta_db['recommendation_metadata']
        meta_doc.fetch()
        if not meta_doc.exists():
            print('recommendation_metadata doc not found in', CL_RECOMMENDDB)
            raise RecommendationsNotGeneratedException
      
        timestamp_str = meta_doc['timestamp_utc']

        import dateutil.parser
        return dateutil.parser.parse(timestamp_str)

    @staticmethod
    def get_realtime_ratings(meta_doc):

        # get the product features
        pf_keys = json.loads(
                        meta_doc.get_attachment('product_feature_keys', attachment_type='text')
                        )

        pf_vals = json.loads(
                        meta_doc.get_attachment('product_feature_vals', attachment_type='text')
                        )

        Vt = np.matrix(np.asarray(pf_vals))

        full_u = np.zeros(len(pf_keys))

        def set_rating(pf_keys, full_u, key, val):
            try:
                full_u[pf_keys.index(key)] = val
            except:
                pass

        # TODO iterate through movies user has rated
        # E.g. Movie.get_ratings(user_id)

        set_rating(pf_keys, full_u, 260, 9),   # Star Wars (1977)
        set_rating(pf_keys, full_u, 1,   8),   # Toy Story (1995)

        recommendations = full_u*Vt*Vt.T

        ratings = list(np.sort(recommendations)[:,-10:].flat)
        ratings = [ str(r) for r in ratings ]

        movie_ids = np.where(recommendations >= np.sort(recommendations)[:,-10:].min())[1]
        movie_ids = [ str(m) for m in movie_ids ]

        return (ratings, movie_ids)


    @staticmethod
    def get_recommendations(user_id):

        recommendation_type = None

        if not current_user.is_authenticated:
            return (recommendation_type, [])


        meta_db = cloudant_client[CL_RECOMMENDDB]

        # get recommendation_metadata document with last run details
        meta_doc = meta_db['recommendation_metadata']
        meta_doc.fetch()
        if not meta_doc.exists():
            print('recommendation_metadata doc not found in', CL_RECOMMENDDB)
            raise RecommendationsNotGeneratedException
       
        # get name of db for latest recommendations
        latest_recommendations_db = meta_doc['latest_db']
  
        try:
            recommendations_db = cloudant_client[latest_recommendations_db]
            if not recommendations_db.exists():
                print('recommendationsdb not found', latest_recommendations_db)
                raise RecommendationsNotGeneratedException
        except KeyError:
            # FIXME - we shouldn't need to do exists() and handle KeyError
            print('recommendationsdb not found', latest_recommendations_db)
            raise RecommendationsNotGeneratedException

        # get recommendations for user
        try:
            recommendations_doc = recommendations_db[user_id]
            movie_ids = [ str(rec[1]) for rec in recommendations_doc['recommendations'] ]
            ratings = [ str(rec[2]) for rec in recommendations_doc['recommendations'] ]

            recommendation_type = "batch"

        except KeyError:
            recommendation_type = "realtime"
            ( ratings, movie_ids ) = Recommendation.get_realtime_ratings(meta_doc)

        # get movie names
        keys = urllib.parse.quote_plus(json.dumps(list(movie_ids)))
        end_point = '{0}/{1}/_all_docs?keys={2}&include_docs=true'.format ( CL_URL, CL_MOVIEDB, keys)
        response = cloudant_client.r_session.get(end_point)
        movie_data = json.loads(response.text)

        recommendations = []

        if 'rows' in movie_data:
            for row in movie_data['rows']:
                if 'doc' in row:
                    movie_id   = row['key']
                    movie_name = row['doc']['name']
                    rating = ratings[movie_ids.index(movie_id)]
                    recommendation = Recommendation(movie_id, movie_name, rating)
                    recommendations.append(recommendation)

        return (recommendation_type, recommendations)


    def as_dict(self):
        return dict(
                    movie_id = self.movie_id,
                    movie_name = self.movie_name,
                    rating = self.rating
                )

class Movie:

    def __init__(self, movie_id, name):
        self.movie_id = movie_id
        self.name = name 
        self.rating = None

    def as_dict(self):
        return dict(
                    movie_id = self.movie_id,
                    name = self.name,
                    rating = self.rating
                )

    @staticmethod
    def save_rating(movie_id, user_id, rating):
        # FIXME: updating a rating currently fails due to MVCC conflict
        data = {
            "_id": "user_{0}/movie_{1}".format(user_id, movie_id),
            "rating": rating,
            "timestamp": current_milli_time()
        }
        response = requests.post(
                RATINGDB_URL,
                auth=app.config['CL_AUTH'], 
                data=json.dumps(data), 
                headers={'Content-Type':'application/json'})

        # print(response.text)
        # TODO check response
        response.raise_for_status()

    @staticmethod
    def find_movies(search_string):

        movie_db = cloudant_client[CL_MOVIEDB]
        index_name = 'movie-search-index'

        end_point = '{0}/{1}/_design/{2}/_search/{2}'.format ( CL_URL, CL_MOVIEDB, index_name )
        data = {
            "q": "name:" + search_string,
            "limit": 25
        }
        headers = { "Content-Type": "application/json" }
        response = cloudant_client.r_session.post(end_point, data=json.dumps(data), headers=headers)
        movie_data = json.loads(response.text)
        if 'rows' in movie_data:
            movies = {}
            rating_ids = []

            for row in movie_data['rows']:
                movie_user_key = "user_{0}/movie_{1}".format(current_user.get_id(), row['id'])

                movies[movie_user_key] = Movie(row['id'], row['fields']['name'])
                if current_user.get_id():
                    rating_ids.append(movie_user_key)

        keys = urllib.parse.quote_plus(json.dumps(rating_ids))
        end_point = '{0}/{1}/_all_docs?keys={2}&include_docs=true'.format ( CL_URL, CL_RATINGDB, keys)
        response = cloudant_client.r_session.get(end_point)
        rating_data = json.loads(response.text)

        if 'rows' in rating_data:
            for row in rating_data['rows']:
                if 'doc' in row:
                    movies[row['key']].rating = row['doc']['rating']

        return [ v for k,v in movies.items()]


class User(UserMixin):

    id = ''
    email = ''
    password_hash = ''
    confirmed = False

    def __init__(self, id, email, password=None, password_hash=None):
        self.id = id 
        self.email = email
        if password_hash:
            self.password_hash = password_hash
        else:
            self.password_hash = generate_password_hash(password)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def email_is_registered(email):
        return User.find_by_email(email) is not None

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def __repr__(self):
        return '<User %r>' % self.email

    def save(self):

        # TODO put this cloudant lookup code into a utility method

        if self.id == None:
            self.id = get_next_user_id()
            data = { 
                "_id": str(self.id),
                "email": self.email,
                "password_hash": self.password_hash
            }
            auth_db = cloudant_client[CL_AUTHDB]
            doc = auth_db.create_document(data)

            if not doc.exists():
                raise BaseException("Coud not save: " + data)
        else:
            raise BaseException("Updating user account is not supported")

    @staticmethod
    def find_by_email(email):

        # TODO put this cloudant lookup code into a utility method

        auth_db = cloudant_client[CL_AUTHDB]
        key = urllib.parse.quote_plus(email)
        view_name = 'authdb-email-index'
        end_point = '{0}/{1}/_design/{2}/_view/{2}?key="{3}"&include_docs=true'.format ( CL_URL, CL_AUTHDB, view_name, key )
        response = cloudant_client.r_session.get(end_point)

        if response.status_code == 200:
            rows = response.json()['rows']
            if len(rows) > 0:
                password_hash = rows[0]['doc']['password_hash']
                id = rows[0]['doc']['_id']
                user = User(id, email, password_hash=password_hash)
                return user
            else:
                print("user not found for email", email)
                return None
        return None

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):

    # TODO put this cloudant lookup code into a utility method

    auth_db = cloudant_client[CL_AUTHDB]
    end_point = '{0}/{1}/{2}'.format ( CL_URL, CL_AUTHDB, user_id )
    response = cloudant_client.r_session.get(end_point)

    if response.status_code == 200:
        doc = response.json()
        email = doc['email']
        password_hash = doc['password_hash']
        user = User(user_id, email, password_hash=password_hash)
        return user
    return None



