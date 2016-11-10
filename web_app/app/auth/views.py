from flask import Flask, render_template, session, redirect, url_for 
from . import forms
from . import auth
from .. import app


@auth.route('/index', methods=['GET', 'POST'])
def index():

    return render_template('/auth/index.html') 

