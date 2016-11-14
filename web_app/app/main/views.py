from flask import Flask, render_template, session, redirect, url_for, request
from flask.ext.login import login_required
from . import forms
from . import main 
from .. import app
from ..models import Album

@main.route('/', methods=['GET', 'POST'])
def index():

    search_string = session.get('search_string') 
    if search_string:
        session['albums'] = Album.find_albums(session.get('search_string'))
    else:
        session['albums'] = []

    return render_template('/main/index.html', 
            name = search_string,
            albums = session.get('albums'))

@main.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    return render_template('/main/recommendations.html')

@main.route('/set_search_string', methods=['POST'])
def set_search_string():
    form = forms.SearchForm()
    session['search_string'] = form.search_string.data
    return redirect(url_for('main.index'))

@main.route('/set_rating', methods=['POST'])
@login_required
def set_rating():

    if not request.json or \
       not 'album_id' in request.json or \
       not 'user_id' in request.json or \
       not 'rating' in request.json:
        abort(400)

    album_id = request.json['album_id']
    user_id  = request.json['user_id']
    rating   = request.json['rating']

    Album.save_rating(album_id, user_id, int(rating))
    return("{ok}")
