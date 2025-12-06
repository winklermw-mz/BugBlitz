from utils.database import db

RESULT_NOT_TESTED = "not tested"
RESULT_OK = "ok"
RESULT_FAILED = "failed"
RESULT_BLOCKED = "blocked"

class TestRunAssignment(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    test_run_id: int = db.Column(db.Integer, db.ForeignKey('test_run.id'), nullable=False)
    test_case_id: int = db.Column(db.Integer, db.ForeignKey('test_case.id', ondelete='CASCADE'), nullable=False)
    tester_id: int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    result: str = db.Column(db.String(50), default=RESULT_NOT_TESTED) 
    comment: str = db.Column(db.Text)
    step_results = db.relationship('TestStepResult', backref='assignment', cascade="all, delete-orphan")
    
    test_case = db.relationship('TestCase', back_populates='assignments')
    tester = db.relationship('User')

    def __init__(self, test_run_id: int, test_case_id: int, tester_id: int):
        self.test_run_id = test_run_id
        self.test_case_id = test_case_id
        self.tester_id = tester_id