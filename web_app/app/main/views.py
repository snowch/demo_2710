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

try:
    vcap = json.loads(os.getenv("VCAP_SERVICES"))['cloudantNoSQLDB']
    cl_user = vcap[0]['credentials']['username']
    cl_pass = vcap[0]['credentials']['password']
    cl_url  = vcap[0]['credentials']['url']
    auth    = ( cl_user, cl_pass )
except:
    print('A Cloudant service is not bound to the application.  Please bind a Cloudant service and try again.')


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
        response = requests.post(cl_url + '/musicdb/_find', 
                    auth=auth, 
                    data=json.dumps(qry), 
                    headers={'Content-Type':'application/json'})

        response.raise_for_status()
        session['albums'] = json.loads(response.text)['docs']
        return redirect(url_for('index'))

    return render_template('index.html', 
            form=form, 
            name=session.get('name'), 
            albums=session.get('albums'))

