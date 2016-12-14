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
from app.messagehub_util import send
import collections

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
        else:
            JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder

class Event:

    LOGIN_EVENT = "LOGIN_EVENT"

    @staticmethod
    def login_event(user_id):
        send("{0},{1}".format(Event.LOGIN_EVENT, user_id))

class Recommendation:

    def __init__(self, movie, rating, timestamp):
        self.movie_id = movie
        self.rating = rating
        self.timestamp = timestamp

    @staticmethod
    def get_recommendations(user_id):

        end_point  = ''
        end_point += '{0}/{1}/_design/{2}/_view/{2}?'.format(CL_URL, CL_RECOMMENDDB, 'latest-recommendation-index')
        end_point += 'descending=true&limit=25&include_docs=true&'
        end_point += 'startkey=[{0},9999999999]&endkey=[{0},0]'.format(user_id)

        response = cloudant_client.r_session.get(end_point)
        recommendation_data = json.loads(response.text)

        # print(recommendation_data)

        recommendations = {}

        processed_movie_ids = []

        if 'rows' in recommendation_data:
            for row in recommendation_data['rows']:
                if 'doc' in row:
                    product   = row['doc']['product'] 
                    rating    = row['doc']['rating']
                    timestamp = row['doc']['timestamp']
 
                    if product not in processed_movie_ids:
                        recommendations[rating] = Recommendation(product, rating, timestamp)
                        processed_movie_ids.append(product)

        # sort by rating
        ordered_recommendations = collections.OrderedDict(sorted(recommendations.items(), reverse=True))

        return [ v for k,v in ordered_recommendations.items()]


    def as_dict(self):
        return dict(
                    movie_id = self.movie_id,
                    name = self.name,
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



