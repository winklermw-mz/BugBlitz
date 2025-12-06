from utils.database import db
from model.role import ROLE_MANAGER, ROLE_TESTER
from flask_login import UserMixin

USER_ADMIN = "admin"

user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

class User(UserMixin, db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(150), unique=True, nullable=False)
    email: str = db.Column(db.String(150), unique=True, nullable=True)
    password_hash: str = db.Column(db.String(150), nullable=False)
    roles = db.relationship('Role', secondary=user_roles, backref='users')

    def __init__(self, username: str, email: str, password_hash: str):
        self.username = username
        self.email = email
        self.password_hash = password_hash

    def has_role(self, role_name):
        return any(r.name == role_name for r in self.roles)
    
    def is_admin(self):
        return self.has_role(USER_ADMIN)

    def is_test_manager(self):
        return self.has_role(ROLE_MANAGER)
    
    def is_tester(self):
        return self.has_role(ROLE_TESTER)