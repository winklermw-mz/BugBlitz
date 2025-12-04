from utils.database import db

ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_TESTER = "tester"

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)