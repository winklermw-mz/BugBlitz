from utils.database import db

class TestStepResult(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    assignment_id: int = db.Column(db.Integer, db.ForeignKey('test_run_assignment.id'), nullable=False)
    step_number: int = db.Column(db.Integer, nullable=False)
    status: str = db.Column(db.String(50))
    comment: str = db.Column(db.Text)

    def __init__(self, assignment_id: int, step_number: int):
        self.assignment_id = assignment_id
        self.step_number = step_number