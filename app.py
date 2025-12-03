import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dein-geheimer-schluessel-hier'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bugbench.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

case_tags = db.Table('case_tags',
    db.Column('case_id', db.Integer, db.ForeignKey('test_case.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    roles = db.relationship('Role', secondary=user_roles, backref='users')

    def has_role(self, role_name):
        return any(r.name == role_name for r in self.roles)
    
    def is_admin(self):
        return self.has_role('admin')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref='projects')

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

class TestStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    action = db.Column(db.Text, nullable=False)
    expected_result = db.Column(db.Text, nullable=False)

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

class TestStepResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('test_run_assignment.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50))
    comment = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_initial_data():
    with app.app_context():
        db.create_all()
        for r_name in ['admin', 'manager', 'tester']:
            if not Role.query.filter_by(name=r_name).first():
                db.session.add(Role(name=r_name))
        db.session.commit()

        if not User.query.filter_by(username='admin').first():
            hashed_pw = generate_password_hash('admin', method='scrypt')
            admin_user = User(username='admin', password_hash=hashed_pw)
            admin_role = Role.query.filter_by(name='admin').first()
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
            db.session.commit()
            print("Admin 'admin' erstellt.")


@app.route('/')
@login_required
def dashboard():
    if current_user.is_admin():
        projects = Project.query.all()
        return render_template('dashboard.html', all_projects=projects)
    
    if current_user.has_role('manager'):
        my_projects = Project.query.filter_by(owner_id=current_user.id).all()
        other_projects = Project.query.filter(Project.owner_id != current_user.id).all()
        return render_template('dashboard.html', my_projects=my_projects, other_projects=other_projects)
    
    projects = Project.query.all()
    return render_template('dashboard.html', all_projects=projects)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Login fehlgeschlagen.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if not current_user.is_admin(): abort(403)
    
    if request.method == 'POST':
        if 'create' in request.form:
            uname = request.form.get('username')
            pwd = request.form.get('password')
            selected_roles = request.form.getlist('roles')
            
            if User.query.filter_by(username=uname).first():
                flash('User existiert bereits.')
            else:
                new_user = User(username=uname, password_hash=generate_password_hash(pwd, method='scrypt'))
                for r_name in selected_roles:
                    r = Role.query.filter_by(name=r_name).first()
                    if r: new_user.roles.append(r)
                db.session.add(new_user)
                db.session.commit()
                flash('Benutzer angelegt.')
        elif 'delete' in request.form:
            User.query.filter_by(id=request.form.get('user_id')).delete()
            db.session.commit()
            
    users = User.query.all()
    all_roles = Role.query.all()
    return render_template('admin.html', users=users, all_roles=all_roles)

@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def create_project():
    if not (current_user.has_role('manager') or current_user.is_admin()): abort(403)
    if request.method == 'POST':
        proj = Project(title=request.form.get('title'), description=request.form.get('description'), owner_id=current_user.id)
        db.session.add(proj)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('project_form.html', project=None)

@app.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    proj = Project.query.get_or_404(project_id)
    if not (current_user.is_admin() or (current_user.has_role('manager') and proj.owner_id == current_user.id)): abort(403)
    db.session.delete(proj)
    db.session.commit()
    flash('Projekt gelöscht.')
    return redirect(url_for('dashboard'))

@app.route('/project/<int:project_id>')
@login_required
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    sorted_cases = TestCase.query.filter_by(project_id=project_id).order_by(TestCase.sequence.asc(), TestCase.id.asc()).all()
    return render_template('project_view.html', project=project, sorted_cases=sorted_cases)

# -- Cases --
@app.route('/project/<int:project_id>/case/new', methods=['GET', 'POST'])
@app.route('/project/<int:project_id>/case/<int:case_id>/edit', methods=['GET', 'POST'])
@login_required
def manage_case(project_id, case_id=None):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_admin() or (current_user.has_role('manager') and project.owner_id == current_user.id)): abort(403)

    case = TestCase.query.get(case_id) if case_id else TestCase(project_id=project.id)

    if request.method == 'POST':
        case.sequence = int(request.form.get('sequence', 0))
        case.title = request.form.get('title')
        case.summary = request.form.get('summary')
        case.precondition = request.form.get('precondition')
        case.postcondition = request.form.get('postcondition')
        case.priority = request.form.get('priority')
        case.source = request.form.get('source')
        
        tag_names = [t.strip() for t in request.form.get('tags', '').split(' ') if t.strip()]
        case.tags = []
        for t_name in tag_names:
            tag = Tag.query.filter_by(name=t_name).first()
            if not tag:
                tag = Tag(name=t_name)
                db.session.add(tag)
            case.tags.append(tag)

        db.session.add(case)
        db.session.commit()
        
        TestStep.query.filter_by(test_case_id=case.id).delete()
        actions = request.form.getlist('action[]')
        results = request.form.getlist('result[]')
        
        for idx, (act, res) in enumerate(zip(actions, results)):
            if act.strip() or res.strip():
                step = TestStep(test_case_id=case.id, step_number=idx+1, action=act, expected_result=res)
                db.session.add(step)
        
        db.session.commit()
        return redirect(url_for('view_project', project_id=project.id))

    all_tags = [t.name for t in Tag.query.all()]
    return render_template('case_form.html', project=project, case=case, all_tags=all_tags)

@app.route('/case/<int:case_id>/delete', methods=['POST'])
@login_required
def delete_case(case_id):
    case = TestCase.query.get_or_404(case_id)
    if not (current_user.is_admin() or (current_user.has_role('manager') and case.project.owner_id == current_user.id)): abort(403)
    db.session.delete(case)
    db.session.commit()
    return redirect(url_for('view_project', project_id=case.project_id))

@app.route('/case/<int:case_id>/sort/<direction>', methods=['POST'])
@login_required
def sort_case(case_id, direction):
    current_case = TestCase.query.get_or_404(case_id)
    project = current_case.project
    
    if not (current_user.is_admin() or (current_user.has_role('manager') and project.owner_id == current_user.id)):
        abort(403)

    sorted_cases = TestCase.query.filter_by(project_id=project.id).order_by(TestCase.sequence.asc(), TestCase.id.asc()).all()
    
    current_index = [i for i, case in enumerate(sorted_cases) if case.id == case_id][0]

    if direction == 'up' and current_index > 0:
        prev_case = sorted_cases[current_index - 1]
        temp_sequence = current_case.sequence
        current_case.sequence = prev_case.sequence
        prev_case.sequence = temp_sequence
        
        db.session.commit()
        flash(f'Testfall "{current_case.title}" wurde nach oben verschoben.')
        
    elif direction == 'down' and current_index < len(sorted_cases) - 1:
        next_case = sorted_cases[current_index + 1]
        temp_sequence = current_case.sequence
        current_case.sequence = next_case.sequence
        next_case.sequence = temp_sequence
        
        db.session.commit()
        flash(f'Testfall "{current_case.title}" wurde nach unten verschoben.')
        
    return redirect(url_for('view_project', project_id=project.id))

@app.route('/project/<int:project_id>/run/new', methods=['GET', 'POST'])
@login_required
def create_run(project_id):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_admin() or (current_user.has_role('manager') and project.owner_id == current_user.id)): abort(403)
         
    if request.method == 'POST':
        run = TestRun(
            project_id=project.id, 
            title=request.form.get('title'),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        )
        db.session.add(run)
        db.session.commit()
        
        for key in request.form:
            if key.startswith('assign_case_'):
                case_id = int(key.replace('assign_case_', ''))
                tester_ids = request.form.getlist(key)
                for tid in tester_ids:
                    assign = TestRunAssignment(test_run_id=run.id, test_case_id=case_id, tester_id=int(tid))
                    db.session.add(assign)
        
        db.session.commit()
        return redirect(url_for('view_project', project_id=project.id))

    potential_testers = User.query.filter(User.roles.any(Role.name.in_(['tester', 'manager', 'admin']))).all()
    return render_template('run_form.html', project=project, testers=potential_testers)

@app.route('/run/<int:run_id>/status', methods=['POST'])
@login_required
def update_run_status(run_id):
    run = TestRun.query.get_or_404(run_id)
    if not (current_user.is_admin() or (current_user.has_role('manager') and run.project.owner_id == current_user.id)): abort(403)
    
    new_status = request.form.get('status')
    if new_status in ['active', 'finished', 'aborted']:
        run.status = new_status
        db.session.commit()
    return redirect(request.referrer)

@app.route('/run/<int:run_id>/execute', methods=['GET', 'POST'])
@login_required
def execute_run(run_id):
    run = TestRun.query.get_or_404(run_id)
    
    if current_user.is_admin() or current_user.has_role('manager'):
        assignments = TestRunAssignment.query.filter_by(test_run_id=run.id).all()
    else:
        assignments = TestRunAssignment.query.filter_by(test_run_id=run.id, tester_id=current_user.id).all()

    all_assigns = TestRunAssignment.query.filter_by(test_run_id=run.id).all()
    stats = {'total': len(all_assigns), 'ok': 0, 'fehlgeschlagen': 0, 'blockiert': 0, 'nicht getestet': 0}
    for a in all_assigns:
        if a.result in stats: stats[a.result] += 1
        else: stats['nicht getestet'] += 1

    if request.method == 'POST':
        assign_id = request.form.get('assignment_id')
        assignment = TestRunAssignment.query.get(assign_id)
        
        allowed = current_user.is_admin() or \
                  (current_user.has_role('manager') and run.project.owner_id == current_user.id) or \
                  (current_user.id == assignment.tester_id and run.status == 'active')
                  
        if assignment and allowed:
            assignment.result = request.form.get('status')
            assignment.comment = request.form.get('comment')
            
            for step in assignment.test_case.steps:
                s_status = request.form.get(f'step_status_{step.step_number}')
                s_comment = request.form.get(f'step_comment_{step.step_number}')
                
                step_res = TestStepResult.query.filter_by(assignment_id=assignment.id, step_number=step.step_number).first()
                if not step_res:
                    step_res = TestStepResult(assignment_id=assignment.id, step_number=step.step_number)
                    db.session.add(step_res)
                
                step_res.status = s_status
                step_res.comment = s_comment
                
            db.session.commit()
            flash('Ergebnis gespeichert.')
            return redirect(url_for('execute_run', run_id=run.id))

    return render_template('execute.html', run=run, assignments=assignments, stats=stats)

if __name__ == '__main__':
    create_initial_data()
    app.run(debug=True)