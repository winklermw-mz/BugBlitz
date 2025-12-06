from utils.database import db
from model.role import ROLE_MANAGER, ROLE_TESTER
from flask_login import UserMixin
from model.run_assignment import TestRunAssignment
from model.project import Project
from model.role import Role

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
    
    def delete(self):
        assignments = TestRunAssignment.query.filter_by(tester_id=self.id).all()
        for assignment in assignments:
            db.session.delete(assignment)
        
        projects = Project.query.filter_by(owner_id=self.id).all()
        for project in projects:
            project.delete()
        
        db.session.delete(self)
        db.session.commit()
    
    def set_roles(self, roles: list):
        for role_name in roles:
            r = Role.query.filter_by(name=role_name).first()
            if r: self.roles.append(r)

    def store(self):
        db.session.add(self)
        db.session.commit()