from utils.database import db
from datetime import date
from model.run_assignment import TestRunAssignment, RESULT_OK, RESULT_BLOCKED, RESULT_FAILED, RESULT_NOT_TESTED

STATE_CREATED = "created"
STATE_ACTIVE = "active"
STATE_FINISHED = "finished"
STATE_ABORTED = "aborted"

class TestRun(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title: str = db.Column(db.String(150), nullable=False)
    start_date: date = db.Column(db.Date)
    end_date: date = db.Column(db.Date)
    status: str = db.Column(db.String(20), default=STATE_CREATED)
    
    assignments = db.relationship('TestRunAssignment', backref='test_run', cascade="all, delete-orphan")
    project = db.relationship('Project', backref='test_runs')

    def __init__(self, project_id: int, title: str, start_date: date, end_date: date):
        self.project_id = project_id
        self.title = title
        self.start_date = start_date
        self.end_date = end_date

    def is_active(self):
        return self.status == STATE_ACTIVE
    
    def is_created(self):
        return self.status == STATE_CREATED
    
    def is_overdue(self):
        return (self.status == STATE_ACTIVE and self.end_date < date.today()) or \
                (self.status == STATE_CREATED and self.start_date < date.today())
    
    def calculate_statistics(self) -> dict:
        all_assigns = TestRunAssignment.query.filter_by(test_run_id=self.id).all()
        count = len(all_assigns)
        stats = {
            "total": count, 
            "percentage": 0,
            "overdue": self.is_overdue(),
            "testers": {},
            RESULT_OK: 0,
            RESULT_FAILED: 0, 
            RESULT_BLOCKED: 0, 
            RESULT_NOT_TESTED: 0,
        }
        for a in all_assigns:
            if a.result in stats: 
                stats[a.result] += 1
            
            if a.result == RESULT_NOT_TESTED:
                user = a.tester
                if user.username not in stats["testers"]:
                    stats["testers"][user.username] = 0
                stats["testers"][user.username] += 1

        stats["percentage"] = 0 if count == 0 else int(round(100 * (count - stats[RESULT_NOT_TESTED]) / count, 0))
        return stats

    def store(self):
        db.session.add(self)
        db.session.commit()

    def set_status(self, status):
        self.status = status
        db.session.commit()