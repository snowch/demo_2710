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
import collections
import numpy as np
from .dao import MovieDAO, RatingDAO, RecommendationDAO, UserDAO, RecommendationsNotGeneratedException, RecommendationsNotGeneratedForUserException


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


class Recommendation:

    def __init__(self, movie_id, movie_name, rating):
        self.movie_id = movie_id
        self.movie_name = movie_name
        self.rating = rating

    @staticmethod
    def get_latest_recommendation_timestamp():
        return RecommendationDAO.get_latest_recommendation_timestamp()

    @staticmethod
    def get_realtime_ratings(user_id, meta_doc):

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
                idx = pf_keys.index(key)
                full_u.itemset(idx, val)
            except ValueError:
                # the movie didn't have any ratings in when the model 
                # when the product features were create last time the 
                # model was trained
                pass
            except:
                import sys
                print("Unexpected error:", sys.exc_info()[0])

        for key, value in Rating.get_ratings(user_id).items():
            set_rating(pf_keys, full_u, key, value)

        recommendations = full_u*Vt*Vt.T

        ratings = list(np.sort(recommendations)[:,-10:].flat)
        ratings = [ str(r) for r in ratings ]

        movie_ids = np.where(recommendations >= np.sort(recommendations)[:,-10:].min())[1]
        movie_ids = [ int(m) for m in movie_ids ]

        return (ratings, movie_ids)


    @staticmethod
    def get_recommendations(user_id):

        recommendation_type = None

        if not current_user.is_authenticated:
            return (recommendation_type, [])

        # get recommendation_metadata document with last run details
        try:
            meta_db = cloudant_client[CL_RECOMMENDDB]
            meta_doc = meta_db['recommendation_metadata']
            meta_doc.fetch()
        except KeyError:
            print('recommendation_metadata doc not found in', CL_RECOMMENDDB)
            raise RecommendationsNotGeneratedException
       
        # get name of db for latest recommendations
        try:
            latest_recommendations_db = meta_doc['latest_db']
            recommendations_db = cloudant_client[latest_recommendations_db]
        except KeyError:
            print('recommendationsdb not found', latest_recommendations_db)
            raise RecommendationsNotGeneratedException

        # get recommendations for user
        try:
            recommendations_doc = recommendations_db[user_id]
            movie_ids = [ int(rec[1]) for rec in recommendations_doc['recommendations'] ]
            ratings = [ str(rec[2]) for rec in recommendations_doc['recommendations'] ]
            recommendation_type = "batch"

        except KeyError:
            ( ratings, movie_ids ) = Recommendation.get_realtime_ratings(user_id, meta_doc)
            recommendation_type = "realtime"

        # we have the movie_ids, let's get the movie names
        recommendations = []
        for movie_id, movie_name in MovieDAO.get_movie_names(movie_ids).items():
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

class Rating:

    @staticmethod
    def get_ratings(user_id):
        return RatingDAO.get_ratings(int(user_id))

    @staticmethod
    def save_rating(movie_id, user_id, rating):
        RatingDAO.save_rating(
                int(movie_id), int(user_id), rating
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
    
    def __repr__(self):
        return str(self.as_dict())

    @staticmethod
    def find_movies(user_id, search_string):

        movies_dict = MovieDAO.find_movies(search_string)

        # the DAO expects movie_ids to be integers
        movie_ids = [ int(m) for m in list(movies_dict.keys()) ]

        # we need to also get the user ratings
        movie_ratings = RatingDAO.get_ratings(user_id, movie_ids)

        # we need to get the user's rating for the movie if available
        movies = []
        for movie_id, movie_name in movies_dict.items():

            movie_id = int(movie_id)

            movie = Movie(
                        movie_id,
                        movie_name,
                        )

            # the user rated this movie
            if movie_id in movie_ratings:
                movie.rating = movie_ratings[movie_id]

            movies.append(movie)

        return movies


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

    @staticmethod
    def email_is_registered(email):
        return User.find_by_email(email) is not None

    def __repr__(self):
        return '<User %r>' % self.email

    def save(self):

        if self.id != None:
            raise BaseException("Updating user account is not supported")

        user_id = UserDAO.create_user(
                                    self.email,
                                    self.password_hash
                                    )
        self.user_id = id

    @staticmethod
    def find_by_email(email):

        user_dict = UserDAO.find_by_email(email)

        if user_dict:
            return User(
                        user_dict['user_id'],
                        email,
                        password_hash=user_dict['password_hash']
                    )
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

    user_dict = UserDAO.load_user(user_id)
    
    if user_dict:
        return User(
                    user_id,
                    user_dict['email'],
                    password_hash=user_dict['password_hash']
                )
    else:
        return None

