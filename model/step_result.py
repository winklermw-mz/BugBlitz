from utils.database import db

class TestStepResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('test_run_assignment.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50))
    comment = db.Column(db.Text)
