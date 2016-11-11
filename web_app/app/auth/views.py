from flask import Flask, render_template, session, redirect, url_for 
from . import forms
from . import auth
from .. import app
from .forms import LoginForm, RegistrationForm
from .. import models


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = models.User(email=form.email.data,
                    password=form.password.data)

        user.save()

        #token = user.generate_confirmation_token()
        # send_email(user.email, 'Confirm Your Account',
        #           'auth/email/confirm', user=user, token=token)
        #flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

