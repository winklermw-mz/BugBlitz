from utils.database import db

PRIORITY_HIGH = "high"
PRIORITY_NORMAL = "normal"
PRIORITY_LOW = "low"

case_tags = db.Table(
    'case_tags',
    db.Column('case_id', db.Integer, db.ForeignKey('test_case.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class TestCase(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    project_id: int = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    sequence: int = db.Column(db.Integer, default=0)
    title: str = db.Column(db.String(150), nullable=False)
    summary: str = db.Column(db.Text)
    precondition: str = db.Column(db.Text)
    postcondition: str = db.Column(db.Text)
    priority: str = db.Column(db.String(20))
    source: str = db.Column(db.String(100))
    steps = db.relationship('TestStep', backref='test_case', cascade="all, delete-orphan", order_by='TestStep.step_number')
    tags = db.relationship('Tag', secondary=case_tags, backref='test_cases')
    project = db.relationship('Project', backref='test_cases')
    assignments = db.relationship('TestRunAssignment', back_populates='test_case', cascade='all, delete-orphan', passive_deletes=True)

    def __init__(
            self, 
            project_id: int, 
            sequence: int = 0,
            title: str = "",
            summary: str = "",
            precondition: str = "",
            postcondition: str = "",
            priority: str = "",
            source: str = "",
            tags: list = []
    ):
        self.project_id = project_id
        self.sequence = sequence
        self.title = title
        self.summary = summary
        self.precondition = precondition
        self.postcondition = postcondition
        self.priority = priority
        self.source = source
        self.tags = tags

    def delete(self):
        for assignment in self.assignments:
            db.session.delete(assignment)

        db.session.delete(self)
        db.session.commit()
    
    def store(self):
        db.session.add(self)
        db.session.commit()