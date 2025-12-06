from utils.database import db
from model.run import STATE_FINISHED, STATE_ABORTED, STATE_ACTIVE, STATE_CREATED
from model.run_assignment import TestRunAssignment, RESULT_NOT_TESTED

class Project(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(150), nullable=False)
    description: str = db.Column(db.Text)
    owner_id: int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref='projects')

    def __init__(self, title: str, description: str, owner_id: int):
        self.title = title
        self.description = description
        self.owner_id = owner_id

    def get_open_runs(self, user) -> dict:
        my_runs = {}
        for run in self.test_runs:
            if run.status == STATE_ABORTED or run.status == STATE_FINISHED:
                continue

            if user.is_tester() and not user.is_test_manager() and run.status == STATE_CREATED:
                continue

            assignments = TestRunAssignment.query.filter_by(test_run_id=run.id).all()
            open_tests = []
            for assignment in assignments:
                if assignment.tester_id == user.id and assignment.result == RESULT_NOT_TESTED:
                    open_tests.append(assignment)
            
            if open_tests or user.is_test_manager():
                my_runs[run.id] = {
                    "run": run, 
                    "open_tests": len(open_tests),
                    "overdue": run.is_overdue(),
                    "state": run.status,
                    "project": self.title,
                }
        return my_runs

    def delete(self):
        run_ids = [run.id for run in self.test_runs]
    
        if run_ids:
            assignments = TestRunAssignment.query.filter(TestRunAssignment.test_run_id.in_(run_ids)).all()
            for assignment in assignments:
                db.session.delete(assignment)

        for run in self.test_runs.copy():
            db.session.delete(run)

        for case in self.test_cases.copy():
            db.session.delete(case)

        db.session.delete(self)
        db.session.commit()

    def store(self):
        db.session.add(self)
        db.session.commit()