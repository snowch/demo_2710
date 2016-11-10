from flask import Flask, render_template, session, redirect, url_for 
from . import forms
from . import main 
from . import models
from .. import app


@main.route('/', methods=['GET', 'POST'])
def index():

    form = forms.NameForm()
    if form.validate_on_submit():
        session['name'] = form.name.data
        session['albums'] = models.Albums.find_albums(session.get('name'))
        return redirect(url_for('main.index'))

    return render_template('/main/index.html', 
            form=form, 
            name=session.get('name'), 
            albums=session.get('albums'))

@main.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    return render_template('/main/coming_soon.html')
