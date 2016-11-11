from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import forms
from . import auth
from .. import app
from .forms import LoginForm, RegistrationForm
from .. import models


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = models.User.find_by_email(form.email.data)

        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')

    return render_template('auth/login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = models.User(form.email.data, form.password.data)

        user.save()

        #token = user.generate_confirmation_token()
        # send_email(user.email, 'Confirm Your Account',
        #           'auth/email/confirm', user=user, token=token)
        #flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

