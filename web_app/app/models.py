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
from . import app, login_manager
from app.cloudant_db import cloudant_client

current_milli_time = lambda: int(round(time.time() * 1000))

RATINGDB_URL = app.config['CL_URL'] + '/' + app.config['CL_RATINGDB']

CL_URL      = app.config['CL_URL']
CL_MOVIEDB  = app.config['CL_MOVIEDB']
CL_AUTHDB   = app.config['CL_AUTHDB']
CL_RATINGDB = app.config['CL_RATINGDB']

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Movie):
            return obj.as_dict()
        else:
            JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder

class Movie:

    def __init__(self, movie_id, name):
        self.movie_id = movie_id
        self.name = name 

    def as_dict(self):
        return dict(
                    movie_id = self.movie_id,
                    name = self.name,
                )

    @staticmethod
    def save_rating(movie_id, user_id, rating):
        data = {
            "_id": "movie_{0}/user_{1}".format(movie_id, user_id),
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
        movie_rows = json.loads(response.text)['rows']
        movies = []
        movie_ids = []

        if movie_rows:
            for row in movie_rows:
                movie = Movie(row['id'], row['fields']['name'])
                movies.append(movie)
                movie_ids.append(row['id'])

        return movies 


class User(UserMixin):

    id = ''
    email = ''
    password_hash = ''
    confirmed = False

    def __init__(self, email, password=None, password_hash=None):
        self.id = email
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

        response = requests.get(app.config['CL_URL'] + '/authdb/' + email, 
            auth=app.config['CL_AUTH'], 
            headers={'Content-Type':'application/json'})

        return response.status_code == 200

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

        doc = { 
            "_id": self.email,
            "password_hash": self.password_hash
        }

        # TODO update if exists
        response = requests.post(app.config['CL_URL'] + '/authdb/', 
            auth=app.config['CL_AUTH'], 
            data=json.dumps(doc),
            headers={'Content-Type':'application/json'})

        response.raise_for_status()

    @staticmethod
    def find_by_email(email):

        response = requests.get(app.config['CL_URL'] + '/authdb/' + email, 
            auth=app.config['CL_AUTH'], 
            headers={'Content-Type':'application/json'})

        if response.status_code == 200:
            password_hash = response.json()['password_hash']
            user = User(email, password_hash=password_hash)
            return user
        else:
            return None

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.find_by_email(user_id)


