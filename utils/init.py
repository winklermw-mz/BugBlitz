from database import db
from model.role import Role
from model.user import User
from werkzeug.security import generate_password_hash


def create_initial_data(app):
    with app.app_context():
        db.create_all()
        for r_name in ['admin', 'manager', 'tester']:
            if not Role.query.filter_by(name=r_name).first(): db.session.add(Role(name=r_name))
        db.session.commit()

        if not User.query.filter_by(username='admin').first():
            hashed_pw = generate_password_hash('admin', method='scrypt')
            admin_user = User(username='admin', email='admin@company.ai', password_hash=hashed_pw)
            admin_role = Role.query.filter_by(name='admin').first()
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
            db.session.commit()
            print("Admin 'admin' erstellt.")
