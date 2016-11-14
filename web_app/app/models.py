from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import g, current_app, request, url_for, jsonify
from flask.json import JSONEncoder
from flask.ext.login import UserMixin, AnonymousUserMixin, current_user
import os, json
import requests
from . import app, login_manager

MUSICDB_URL  = app.config['CL_URL'] + '/' + app.config['CL_MUSICDB']
RATINGDB_URL = app.config['CL_URL'] + '/' + app.config['CL_RATINGDB']


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Album):
            return obj.as_dict()
        else:
            JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder

class Album:


    def __init__(self, album_id, artist, title):
        self.album_id = album_id
        self.artist = artist
        self.title = title
        self.rating = None
        self.rating_timestamp = None

    def as_dict(self):
        return dict(
                    album_id=self.album_id,
                    artist=self.artist,
                    title=self.title,
                    rating=self.rating,
                    rating_timestamp=self.rating_timestamp
                )

    @staticmethod
    def find_albums(name):

        qry = { 
            "selector": {
              "$text": name
            }
        }
        response = requests.post(MUSICDB_URL + '/_find', 
                    auth=app.config['CL_AUTH'], 
                    data=json.dumps(qry), 
                    headers={'Content-Type':'application/json'})
        
        album_docs = json.loads(response.text)['docs']
        album_ids = [ doc['_id'] for doc in album_docs ]

        albums = {}
        for doc in album_docs:
            album = Album(doc['_id'], doc['artist'], doc['title'])
            albums[album.album_id] = album
            #print(doc['_id'], doc['artist'], doc['title'])

        if current_user:
            # FIXME: cloudant query appears to be broken so we filter data
            # in our application code. cloudant M/R index will probably be
            # better here
            current_user_id = current_user.get_id()
            qry = { 
                  "selector": {
                       "user_id": { "$eq": current_user_id },
                       "album_id": { "$in": album_ids },
                       "timestamp": { "$gt": None }
                  },
                  "fields": [ "user_id", "album_id", "timestamp", "rating" ],
                  #"sort": [ 
                  #    { "user_id": "desc" },
                  #    { "album_id": "desc" },
                  #    { "timestamp": "desc" }
                  #],
                  #"limit": 1
            }
            # print(json.dumps(qry))

            response = requests.post(RATINGDB_URL + '/_find', 
                        auth=app.config['CL_AUTH'], 
                        data=json.dumps(qry), 
                        headers={'Content-Type':'application/json'})

            # print(response.text)
            # FIXME see output from print statement
            # "warning":"no matching index found, create an index to optimize query time"

            # add rating to album if exists filtering out older timestamps
            # as required due to cloudant query issue
            docs = response.json()['docs']
            if docs:
                for doc in docs:
                    album_id = doc['album_id']
                    rating   = doc['rating']
                    timestamp = doc['timestamp']
                    
                    album = albums[album_id]
                    if album.rating_timestamp is None or \
                       album.rating_timestamp < timestamp:

                        album.rating = rating
                        album.rating_timestamp = timestamp

        return [ v for k,v in albums.items()]


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


