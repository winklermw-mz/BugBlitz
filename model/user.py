from database import db
from flask_login import UserMixin


user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    password_hash = db.Column(db.String(150), nullable=False)
    roles = db.relationship('Role', secondary=user_roles, backref='users')

    def has_role(self, role_name):
        return any(r.name == role_name for r in self.roles)
    
    def is_admin(self):
        return self.has_role('admin')