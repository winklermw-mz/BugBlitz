from database import db


case_tags = db.Table(
    'case_tags',
    db.Column('case_id', db.Integer, db.ForeignKey('test_case.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class TestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    sequence = db.Column(db.Integer, default=0)
    title = db.Column(db.String(150), nullable=False)
    summary = db.Column(db.Text)
    precondition = db.Column(db.Text)
    postcondition = db.Column(db.Text)
    priority = db.Column(db.String(20))
    source = db.Column(db.String(100))
    steps = db.relationship('TestStep', backref='test_case', cascade="all, delete-orphan", order_by='TestStep.step_number')
    tags = db.relationship('Tag', secondary=case_tags, backref='test_cases')
    project = db.relationship('Project', backref='test_cases')