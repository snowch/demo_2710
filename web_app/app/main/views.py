from flask import Flask, render_template, session, redirect, url_for 
from . import forms
from . import main 
from .. import app
from .. import models

@main.route('/', methods=['GET', 'POST'])
def index():

    search_string = session.get('search_string') 
    print('search_string', search_string)
    if search_string:
        session['albums'] = models.Albums.find_albums(session.get('search_string'))
    else:
        session['albums'] = []

    return render_template('/main/index.html', 
            name = search_string,
            albums = session.get('albums'))

@main.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    return render_template('/main/recommendations.html')

@main.route('/set_search_string', methods=['GET', 'POST'])
def set_search_string():
    form = forms.SearchForm()
    session['search_string'] = form.search_string.data
    print(" session['search_string']",  session['search_string'])
    return redirect(url_for('main.index'))
