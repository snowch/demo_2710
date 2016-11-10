from flask import Flask, render_template, session, redirect, url_for, flash
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask_sslify import SSLify

app = Flask(__name__)
sslify = SSLify(app)

app.config.from_object('config.Config')

bootstrap = Bootstrap(app)
moment = Moment(app)

from .main import views
from .main import forms
