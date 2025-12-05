from utils.database import db
from datetime import date
from model.run_assignment import TestRunAssignment, RESULT_OK, RESULT_BLOCKED, RESULT_FAILED, RESULT_NOT_TESTED

STATE_CREATED = "created"
STATE_ACTIVE = "active"
STATE_FINISHED = "finished"
STATE_ABORTED = "aborted"

class TestRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default=STATE_CREATED)
    assignments = db.relationship('TestRunAssignment', backref='test_run', cascade="all, delete-orphan")
    project = db.relationship('Project', backref='test_runs')

    def is_active(self):
        return self.status == STATE_ACTIVE
    
    def is_created(self):
        return self.status == STATE_CREATED
    
    def calculate_statistics(self) -> dict:
        all_assigns = TestRunAssignment.query.filter_by(test_run_id=self.id).all()
        count = len(all_assigns)
        stats = {
            "total": count, 
            "percentage": 0,
            "overdue": self.status == STATE_ACTIVE and self.end_date < date.today(),
            RESULT_OK: 0,
            RESULT_FAILED: 0, 
            RESULT_BLOCKED: 0, 
            RESULT_NOT_TESTED: 0,
        }
        for a in all_assigns:
            if a.result in stats: stats[a.result] += 1
            else: stats[RESULT_NOT_TESTED] += 1
        stats["percentage"] = 0 if count == 0 else int(round(100 * (count - stats[RESULT_NOT_TESTED]) / count, 0))
        return stats
