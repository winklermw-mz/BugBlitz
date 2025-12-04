from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = None

def setup_database(app):
    global db
    db = SQLAlchemy(app)
    return db

def setup_login_manager(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    return login_manager