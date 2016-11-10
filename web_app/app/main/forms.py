from flask import Flask, render_template, session, redirect, url_for, flash
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required

class NameForm(Form):
    name = StringField('Enter search string', validators=[Required()])
    submit = SubmitField('Submit')

