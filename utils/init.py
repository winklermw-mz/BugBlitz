from database import db
from model.role import Role, ROLE_MANAGER, ROLE_TESTER, ROLE_ADMIN
from model.user import User, USER_ADMIN
from werkzeug.security import generate_password_hash


def create_initial_data(app):
    with app.app_context():
        db.create_all()
        for r_name in [ROLE_ADMIN, ROLE_MANAGER, ROLE_TESTER]:
            if not Role.query.filter_by(name=r_name).first(): db.session.add(Role(name=r_name))
        db.session.commit()

        if not User.query.filter_by(username=USER_ADMIN).first():
            hashed_pw = generate_password_hash(USER_ADMIN, method='scrypt')
            admin_user = User(username=USER_ADMIN, email='admin@company.ai', password_hash=hashed_pw)
            admin_role = Role.query.filter_by(name=USER_ADMIN).first()
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created administrator account '{USER_ADMIN}'.")
