from utils.database import db
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user
from werkzeug.security import generate_password_hash
from model.user import User, USER_ADMIN
from model.role import Role

# ROUTE: User administration: create and delete users
def route_user_administration():
    if not current_user.is_admin(): 
        abort(403)
    
    if request.method == 'POST':
        if 'create' in request.form:
            username = str(request.form.get('username'))
            pwd = str(request.form.get('password'))
            pwd2 = str(request.form.get('password_repeat'))
            email = str(request.form.get('email'))
            roles = request.form.getlist('roles')
            
            if pwd != pwd2:
                flash('Error: Passwords do not match.')
                return redirect(url_for('admin_users'))

            if User.query.filter_by(username=username).first():
                flash('Error: User already exists.')
            else:
                user = User(username, email, pwd)
                user.set_roles(roles)
                user.store()
                flash(f"User '{user.username}' successfully created.")
        
        elif 'delete' in request.form:
            user: User = User.query.get(str(request.form.get('user_id')))
            username = user.username
            user.delete()
            flash(f"Deleted user '{username}'")
            
    users = User.query.all()
    all_roles = Role.query.all()
    return render_template('admin.html', users=users, all_roles=all_roles, admin_id=USER_ADMIN)

# ROUTE: Modify user
def route_user_edit(user_id: int):
    if not current_user.is_admin():
        abort(403)

    user = User.query.get_or_404(user_id)
    all_roles = Role.query.all()

    if request.method == 'POST':
        username = str(request.form.get('username'))
        email = str(request.form.get('email'))
        roles = request.form.getlist('roles')
        pwd = str(request.form.get('password'))
        pwd2 = str(request.form.get('password_repeat'))

        if pwd or pwd2:
            if pwd != pwd2:
                flash("Error: Passwords do not match.")
                return redirect(url_for('edit_user', user_id=user.id))
            user.password_hash = generate_password_hash(pwd, method='scrypt')

        user.username = username
        user.email = email
        user.roles = []
        for role_name in roles:
            r = Role.query.filter_by(name=role_name).first()
            if r:
                user.roles.append(r)

        db.session.commit()
        flash("User updated.")
        return redirect(url_for('admin_users'))

    return render_template('user_form.html', user=user, all_roles=all_roles)
