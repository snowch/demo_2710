from flask import Flask, render_template, session, redirect, url_for
import os, json
import requests
from . import forms
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
        old_name = session.get('name')
        #if old_name is not None and old_name != form.name.data:
        #    flash('Looks like you have changed your name!')
        session['name'] = form.name.data
        qry = { 
            "selector": {
              "$text": session.get('name')
            }
        }
        response = requests.post(app.config['CL_URL'] + '/musicdb/_find', 
                    auth=app.config['CL_AUTH'], 
                    data=json.dumps(qry), 
                    headers={'Content-Type':'application/json'})

        response.raise_for_status()
        session['albums'] = json.loads(response.text)['docs']
        return redirect(url_for('index'))

    return render_template('index.html', 
            form=form, 
            name=session.get('name'), 
            albums=session.get('albums'))

