from flask import redirect, url_for
from flask_login import logout_user

# ROUTE: Logout, redirected to login
def route_logout():
    logout_user()
    return redirect(url_for('login'))
