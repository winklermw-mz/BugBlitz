from utils.database import db

class Tag(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(50), unique=True)

    def __init__(self, name: str):
        self.name = name