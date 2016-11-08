from flask import Flask, render_template, session, redirect, url_for, flash
from flask.ext.script import Manager, Server
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required
import os, json
import requests

port = os.getenv('VCAP_APP_PORT', '5000')
vcap = json.loads(os.getenv("VCAP_SERVICES"))['cloudantNoSQLDB']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

server = Server(host="0.0.0.0", port=port)

manager = Manager(app)
manager.add_command("runserver", server)

bootstrap = Bootstrap(app)
moment = Moment(app)

try:
    cl_user = vcap[0]['credentials']['username']
    cl_pass = vcap[0]['credentials']['password']
    cl_url  = vcap[0]['credentials']['url']
    auth    = ( cl_user, cl_pass )
except:
    raise 'A Cloudant service is not bound to the application.  Please bind a Cloudant service and try again.'

class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        session['name'] = form.name.data
        qry = { 
            "selector": {
              "$text": session.get('name')
            }
        }
        response = requests.post(cl_url + '/musicdb/_find', auth=auth, data=json.dumps(qry), headers={'Content-Type':'application/json'})
        response.raise_for_status()
        session['albums'] = json.loads(response.text)['docs']
        return redirect(url_for('index'))

    return render_template('index.html', form=form, name=session.get('name'), albums=session.get('albums'))


if __name__ == '__main__':
    manager.run()
