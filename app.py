from database import setup_database, setup_login_manager
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dein-geheimer-schluessel-hier'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bugbench.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = setup_database(app)
login_manager = setup_login_manager(app)

from model.user import User
from model.role import Role, ROLE_ADMIN, ROLE_MANAGER, ROLE_TESTER
from model.tag import Tag
from model.project import Project
from model.case import TestCase
from model.step import TestStep
from model.run import TestRun
from model.run_assignment import TestRunAssignment
from model.step_result import TestStepResult
from utils.init import create_initial_data


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def dashboard():
    if current_user.is_admin():
        projects = Project.query.all()
        return render_template('dashboard.html', all_projects=projects)
    
    if current_user.has_role(ROLE_MANAGER):
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
            pwd2 = request.form.get('password_repeat')
            email = request.form.get('email')
            selected_roles = request.form.getlist('roles')
            
            if pwd != pwd2:
                flash('Passwörter stimmen nicht überein.')
                return redirect(url_for('admin_users'))

            if User.query.filter_by(username=uname).first():
                flash('User existiert bereits.')
            else:
                new_user = User(username=uname, email=email, password_hash=generate_password_hash(pwd, method='scrypt'))
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

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin():
        abort(403)

    user = User.query.get_or_404(user_id)
    all_roles = Role.query.all()

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        roles = request.form.getlist('roles')

        pwd = request.form.get('password')
        pwd2 = request.form.get('password_repeat')

        if pwd or pwd2:
            if pwd != pwd2:
                flash("Passwörter stimmen nicht überein.")
                return redirect(url_for('edit_user', user_id=user.id))
            user.password_hash = generate_password_hash(pwd, method='scrypt')

        user.username = username
        user.email = email

        user.roles = []
        for role_name in roles:
            r = Role.query.filter_by(name=role_name).first()
            if r:
                user.roles.append(r)

        db.session.commit()
        flash("Benutzer aktualisiert.")
        return redirect(url_for('admin_users'))

    return render_template('user_form.html', user=user, all_roles=all_roles)

@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def create_project():
    if not (current_user.has_role(ROLE_MANAGER) or current_user.is_admin()): abort(403)
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
    if not (current_user.is_admin() or (current_user.has_role(ROLE_MANAGER) and proj.owner_id == current_user.id)): abort(403)
    db.session.delete(proj)
    db.session.commit()
    flash('Projekt gelöscht.')
    return redirect(url_for('dashboard'))

@app.route('/project/<int:project_id>')
@login_required
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    sorted_cases = TestCase.query.filter_by(project_id=project_id).order_by(TestCase.sequence.asc(), TestCase.id.asc()).all()

    statistics = {}
    for run in project.test_runs:
        statistics[run.id] = run.calculate_statistics()
    print(statistics)

    return render_template('project_view.html', project=project, sorted_cases=sorted_cases, statistics=statistics)

@app.route('/project/<int:project_id>/case/new', methods=['GET', 'POST'])
@app.route('/project/<int:project_id>/case/<int:case_id>/edit', methods=['GET', 'POST'])
@login_required
def manage_case(project_id, case_id=None):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_admin() or (current_user.has_role(ROLE_MANAGER) and project.owner_id == current_user.id)): abort(403)

    if case_id:
        case = TestCase.query.get(case_id)
    else:
        case = TestCase(project_id=project.id)
        max_seq = db.session.query(db.func.max(TestCase.sequence)).filter_by(project_id=project.id).scalar()
        case.sequence = (max_seq or 0) + 1


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
    if not (current_user.is_admin() or (current_user.has_role(ROLE_MANAGER) and case.project.owner_id == current_user.id)): abort(403)
    db.session.delete(case)
    db.session.commit()
    return redirect(url_for('view_project', project_id=case.project_id))

@app.route('/case/<int:case_id>/sort/<direction>', methods=['POST'])
@login_required
def sort_case(case_id, direction):
    current_case = TestCase.query.get_or_404(case_id)
    project = current_case.project
    
    if not (current_user.is_admin() or (current_user.has_role(ROLE_MANAGER) and project.owner_id == current_user.id)):
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
    if not (current_user.is_admin() or (current_user.has_role(ROLE_MANAGER) and project.owner_id == current_user.id)): abort(403)
         
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

    potential_testers = User.query.filter(User.roles.any(Role.name.in_([ROLE_TESTER, ROLE_MANAGER, ROLE_ADMIN]))).all()
    return render_template('run_form.html', project=project, testers=potential_testers)

@app.route('/run/<int:run_id>/status', methods=['POST'])
@login_required
def update_run_status(run_id):
    run = TestRun.query.get_or_404(run_id)
    if not (current_user.is_admin() or (current_user.has_role(ROLE_MANAGER) and run.project.owner_id == current_user.id)): abort(403)
    
    new_status = request.form.get('status')
    if new_status in ['active', 'finished', 'aborted']:
        run.status = new_status
        db.session.commit()
    return redirect(request.referrer)

@app.route('/run/<int:run_id>/execute', methods=['GET', 'POST'])
@login_required
def execute_run(run_id):
    run = TestRun.query.get_or_404(run_id)
    
    if current_user.is_admin() or current_user.has_role(ROLE_MANAGER):
        assignments = TestRunAssignment.query.filter_by(test_run_id=run.id).all()
    else:
        assignments = TestRunAssignment.query.filter_by(test_run_id=run.id, tester_id=current_user.id).all()

    stats = run.calculate_statistics()

    if request.method == 'POST':
        assign_id = request.form.get('assignment_id')
        assignment = TestRunAssignment.query.get(assign_id)
        
        allowed = current_user.is_admin() or \
                  (current_user.has_role(ROLE_MANAGER) and run.project.owner_id == current_user.id) or \
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
    create_initial_data(app)
    app.run(debug=True)