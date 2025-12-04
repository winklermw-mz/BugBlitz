from database import db


class TestStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    action = db.Column(db.Text, nullable=False)
    expected_result = db.Column(db.Text, nullable=False)
