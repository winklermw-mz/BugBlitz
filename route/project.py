from flask import render_template, redirect, url_for, request, abort, flash
from flask_login import current_user
from model.project import Project, STATE_ABORTED, STATE_ACTIVE, STATE_CREATED, STATE_FINISHED
from model.testcase import TestCase, PRIORITY_HIGH, PRIORITY_LOW, PRIORITY_NORMAL
from model.run_assignment import RESULT_BLOCKED, RESULT_FAILED, RESULT_NOT_TESTED, RESULT_OK

# ROUTE: New project
def route_project_create():
    if not (current_user.is_test_manager() or current_user.is_admin()): 
        abort(403)

    if request.method == 'POST':
        project = Project(
            title=str(request.form.get('title')), 
            description=str(request.form.get('description')), 
            owner_id=current_user.id
        )
        project.store()
        return redirect(url_for('dashboard'))
    
    return render_template('project_form.html', project=None)

# ROUTE: Delete project, redirected to dashboard
def route_project_delete(project_id: int):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_admin() or (current_user.is_test_manager() and project.owner_id == current_user.id)): 
        abort(403)
    
    project.delete()
    flash('Project successfully deleted.')
    return redirect(url_for('dashboard'))

# ROUTE: Modify tests cases and test plans of an existing project
def route_project_view(project_id: int):
    project = Project.query.get_or_404(project_id)
    sorted_cases = TestCase.query.filter_by(project_id=project_id).order_by(TestCase.sequence.asc(), TestCase.id.asc()).all()

    statistics = {}
    for run in project.test_runs:
        statistics[run.id] = run.calculate_statistics()

    return render_template(
        'project_view.html', 
        project=project, 
        sorted_cases=sorted_cases, 
        statistics=statistics, 
        prio1=PRIORITY_HIGH, 
        prio2=PRIORITY_NORMAL, 
        prio3=PRIORITY_LOW, 
        not_tested=RESULT_NOT_TESTED, 
        blocked=RESULT_BLOCKED, 
        failed=RESULT_FAILED, 
        ok=RESULT_OK, 
        active=STATE_ACTIVE, 
        finished=STATE_FINISHED, 
        aborted=STATE_ABORTED,
        created=STATE_CREATED
    )