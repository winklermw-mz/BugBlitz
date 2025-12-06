from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user
from werkzeug.security import check_password_hash
from model.user import User

# ROUTE: Login form, redirected to dashboard
def route_login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password_hash, str(request.form.get('password'))):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Error: Login failed.')
    return render_template('login.html')
