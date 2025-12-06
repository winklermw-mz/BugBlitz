from utils.database import db

class TestStep(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    test_case_id: int = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)
    step_number: int = db.Column(db.Integer, nullable=False)
    action: str = db.Column(db.Text, nullable=False)
    expected_result: str = db.Column(db.Text, nullable=False)

    def __init__(self, test_case_id: int, step_number: int, action: str, expected_result: str):
        self.test_case_id = test_case_id
        self.step_number = step_number
        self.action = action
        self.expected_result = expected_result