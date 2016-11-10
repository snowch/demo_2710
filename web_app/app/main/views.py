from flask import Flask, render_template, session, redirect, url_for, make_response
from . import forms
from . import models
from .. import app

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET', 'POST'])
def index():

    form = forms.NameForm()
    if form.validate_on_submit():
        session['name'] = form.name.data
        session['albums'] = models.Albums.find_albums(session.get('name'))
        return redirect(url_for('index'))

    return render_template('index.html', 
            form=form, 
            name=session.get('name'), 
            albums=session.get('albums'))

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    return render_template('coming_soon.html')
