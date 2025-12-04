from database import db
from model.run_assignment import TestRunAssignment


class TestRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active') # active, finished, aborted
    assignments = db.relationship('TestRunAssignment', backref='test_run', cascade="all, delete-orphan")
    project = db.relationship('Project', backref='test_runs')

    def is_active(self):
        return self.status == "active"
    
    def calculate_statistics(self) -> dict:
        all_assigns = TestRunAssignment.query.filter_by(test_run_id=self.id).all()
        count = len(all_assigns)
        stats = {
            'total': count, 
            'percentage': 0,
            'ok': 0,
            'fehlgeschlagen': 0, 
            'blockiert': 0, 
            'open': 0,
        }
        for a in all_assigns:
            if a.result in stats: stats[a.result] += 1
            else: stats['open'] += 1
        stats["percentage"] = 0 if count == 0 else int(round(100 * (count - stats["open"]) / count, 0))
        return stats
