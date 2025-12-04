from database import db


class TestRunAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_run_id = db.Column(db.Integer, db.ForeignKey('test_run.id'), nullable=False)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)
    tester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    result = db.Column(db.String(50), default='nicht getestet') 
    comment = db.Column(db.Text)
    step_results = db.relationship('TestStepResult', backref='assignment', cascade="all, delete-orphan")
    
    test_case = db.relationship('TestCase')
    tester = db.relationship('User')
