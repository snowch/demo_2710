from flask import Flask, render_template, session, redirect, url_for, request
from flask.ext.login import login_required, current_user
from . import forms
from . import main 
from .. import app
from ..models import Movie, Recommendation

@main.route('/', methods=['GET', 'POST'])
def index():

    search_string = session.get('search_string') 
    if search_string:
        session['movies'] = Movie.find_movies(session.get('search_string'))
    else:
        session['movies'] = []

    return render_template('/main/index.html', 
            name = search_string,
            movies = session.get('movies'))

@main.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    recommendations = Recommendation.get_recommendations(current_user.get_id())
    return render_template('/main/recommendations.html', recommendations=recommendations)

@main.route('/set_search_string', methods=['POST'])
def set_search_string():
    form = forms.SearchForm()
    session['search_string'] = form.search_string.data
    return redirect(url_for('main.index'))

@main.route('/set_rating', methods=['POST'])
@login_required
def set_rating():

    if not request.json or \
       not 'movie_id' in request.json or \
       not 'user_id' in request.json or \
       not 'rating' in request.json:
        abort(400)

    movie_id = request.json['movie_id']
    user_id  = request.json['user_id']
    rating   = request.json['rating']

    if rating == '-':
        return('{ "success": "ignored_as_value_not_changed" }')

    Movie.save_rating(movie_id, user_id, int(rating))
    return('{ "success": "true" }')
