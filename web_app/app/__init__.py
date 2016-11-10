from flask import Flask, render_template, session, redirect, url_for, flash
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment

app = Flask(__name__)

app.config.from_object('config.Config')

bootstrap = Bootstrap(app)
moment = Moment(app)

from .main import views
from .main import forms
