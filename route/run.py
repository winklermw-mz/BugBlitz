from utils.database import db
from flask import redirect, url_for, abort, render_template, flash, request
from flask_login import current_user
from datetime import datetime
from model.testcase import PRIORITY_HIGH, PRIORITY_LOW, PRIORITY_NORMAL
from model.project import STATE_ABORTED, STATE_ACTIVE, STATE_CREATED, STATE_FINISHED
from model.run import TestRun
from model.role import Role, ROLE_TESTER, ROLE_MANAGER
from model.user import User
from model.run import TestRun
from model.run_assignment import TestRunAssignment, RESULT_NOT_TESTED, RESULT_BLOCKED, RESULT_FAILED, RESULT_OK
from model.project import Project
from model.step_result import TestStepResult
from model.testcase import TestCase

# ROUTE: Modify existing test run (only possible in state "created")
def route_run_edit(run_id: int):
    run = TestRun.query.get_or_404(run_id)
    project = run.project

    if not (current_user.is_admin() or (current_user.is_test_manager() and project.owner_id == current_user.id)): 
        abort(403)
        
    if run.status != STATE_CREATED:
        flash(f'Error: Test Plan must be in status "{STATE_CREATED}" for editing assignments.', 'error')
        return redirect(url_for('execute_run', run_id=run.id))
    
    current_assignments = {}
    for assignment in run.assignments:
        if assignment.test_case_id not in current_assignments:
            current_assignments[assignment.test_case_id] = []
        current_assignments[assignment.test_case_id].append(assignment.tester_id)
         
    potential_testers = User.query.filter(User.roles.any(Role.name.in_([ROLE_TESTER, ROLE_MANAGER]))).all()
    
    return render_template(
        'run_form.html', 
        project=project, 
        run=run,
        testers=potential_testers, 
        current_assignments=current_assignments,
        prio1=PRIORITY_HIGH, 
        prio2=PRIORITY_NORMAL, 
        prio3=PRIORITY_LOW
    )

# ROUTE: Update existing test run
def route_run_update(run_id: int):
    run = TestRun.query.get_or_404(run_id)
    project = run.project

    if not (current_user.is_admin() or (current_user.is_test_manager() and project.owner_id == current_user.id)): 
        abort(403)
        
    if run.status != STATE_CREATED:
        flash(f'Error: Test Plan must be in status "{STATE_CREATED}" for updating assignments.', 'error')
        return redirect(url_for('execute_run', run_id=run.id))
        
    run.title = request.form.get('title')
    run.start_date = datetime.strptime(str(request.form.get('start_date')), '%Y-%m-%d').date()
    run.end_date = datetime.strptime(str(request.form.get('end_date')), '%Y-%m-%d').date()
    
    existing_assignments = TestRunAssignment.query.filter_by(test_run_id=run.id).all()
    
    for key in request.form:
        if key.startswith('assign_case_'):
            case_id = int(key.replace('assign_case_', ''))
            tester_ids = request.form.getlist(key)
            for tid in tester_ids:
                if not tid.strip():
                    continue

                tester_id = int(tid)
                current = TestRunAssignment.query.filter_by(
                    test_run_id=run.id, 
                    tester_id=tester_id,
                    test_case_id=case_id
                ).first()
                
                if not current:
                    assign = TestRunAssignment(test_run_id=run.id, test_case_id=case_id, tester_id=tester_id)
                    db.session.add(assign)
                else:
                    if current in existing_assignments:
                        existing_assignments = [a for a in existing_assignments if a.id != current.id]
            
    for assignment in existing_assignments:
        candidate = TestRunAssignment.query.get(assignment.id)
        if candidate is not None:
            candidate.delete()
    
    db.session.commit()
    flash('Test Plan updated and assignments have been modified.')
    return redirect(url_for('execute_run', run_id=run.id))

# ROUTE: New test run
def route_run_create(project_id: int):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_admin() or (current_user.is_test_manager() and project.owner_id == current_user.id)): 
        abort(403)
        
    if request.method == 'POST':
        run = TestRun(
            project_id=project.id, 
            title=str(request.form.get('title')),
            start_date=datetime.strptime(str(request.form.get('start_date')), '%Y-%m-%d').date(),
            end_date=datetime.strptime(str(request.form.get('end_date')), '%Y-%m-%d').date()
        )
        run.store()
        
        for key in request.form:
            if key.startswith('assign_case_'):
                case_id = int(key.replace('assign_case_', ''))
                tester_ids = request.form.getlist(key)
                for tid in tester_ids:
                    if not tid.strip():
                        continue

                    assign = TestRunAssignment(test_run_id=run.id, test_case_id=case_id, tester_id=int(tid))
                    db.session.add(assign)
        
        db.session.commit()
        flash(f'New test Plan "{run.title}" created.')
        return redirect(url_for('view_project', project_id=project.id))

    potential_testers = User.query.filter(User.roles.any(Role.name.in_([ROLE_TESTER, ROLE_MANAGER]))).all()
    return render_template(
        'run_form.html', 
        project=project, 
        testers=potential_testers, 
        prio1=PRIORITY_HIGH, 
        prio2=PRIORITY_NORMAL, 
        prio3=PRIORITY_LOW
    )

# ROUTE: Update state of test run, redirect to referrer
def route_run_update_state(run_id: int):
    run = TestRun.query.get_or_404(run_id)
    if not (current_user.is_admin() or (current_user.is_test_manager() and run.project.owner_id == current_user.id)): 
        abort(403)
    
    new_status = request.form.get('status')

    if new_status in [STATE_CREATED, STATE_ACTIVE, STATE_FINISHED, STATE_ABORTED]:
        if new_status == STATE_ACTIVE and run.status == STATE_CREATED:
            run.set_status(STATE_ACTIVE)
            flash(f'Test plan "{run.title}" activated.')
            return redirect(request.referrer)

        if new_status == STATE_CREATED and run.status == STATE_ACTIVE:
            run.set_status(STATE_CREATED)
            flash(f'Test plan "{run.title}" reset to created state for adjustments.')
            return redirect(request.referrer)
            
        if new_status == STATE_FINISHED and run.status == STATE_ACTIVE:
            all_assigns = TestRunAssignment.query.filter_by(test_run_id=run_id).all()
            for assignment in all_assigns:
                if assignment.result == RESULT_NOT_TESTED:
                    flash("Error: Cannot close test plan because at least one test case is open.")
                    return redirect(url_for('execute_run', run_id=run_id))

            run.set_status(STATE_FINISHED)
            flash(f'Test plan "{run.title}" finished.')
            return redirect(request.referrer)
            
        if new_status == STATE_ABORTED and run.status == STATE_ACTIVE:
            run.set_status(STATE_ABORTED)
            flash(f'Test plan "{run.title}" aborted.')
            return redirect(request.referrer)
        
        if new_status == STATE_ACTIVE and (run.status == STATE_ABORTED or run.status == STATE_FINISHED):
            run.set_status(STATE_ACTIVE)
            flash(f'Test plan "{run.title}" restarted.')
            return redirect(request.referrer)

    return redirect(request.referrer)

# ROUTE: Execute test run
def route_run_execute(run_id: int):
    run = TestRun.query.get_or_404(run_id)
    
    if current_user.is_admin() or current_user.is_test_manager():
        assignments = TestRunAssignment.query \
            .filter_by(test_run_id=run.id) \
            .join(TestRunAssignment.test_case) \
            .join(TestRunAssignment.tester) \
            .order_by(TestCase.title.asc(), User.username.asc()) \
            .all()
    else:
        assignments = TestRunAssignment.query \
            .filter_by(test_run_id=run.id, tester_id=current_user.id) \
            .filter_by(test_run_id=run.id) \
            .join(TestRunAssignment.test_case) \
            .join(TestRunAssignment.tester) \
            .order_by(TestCase.title.asc(), User.username.asc()) \
            .all()

    stats = run.calculate_statistics()

    if request.method == 'POST':
        assign_id = request.form.get('assignment_id')
        assignment = TestRunAssignment.query.get(assign_id)
        
        allowed = current_user.is_admin() or \
                  (current_user.is_test_manager() and run.project.owner_id == current_user.id) or \
                  (current_user.id == assignment.tester_id and run.status == STATE_ACTIVE)
                  
        if assignment and allowed:
            assignment.result = request.form.get('status')
            assignment.comment = request.form.get('comment')
            
            for step in assignment.test_case.steps:
                s_status = str(request.form.get(f'step_status_{step.step_number}'))
                s_comment = str(request.form.get(f'step_comment_{step.step_number}'))
                
                step_res = TestStepResult.query.filter_by(assignment_id=assignment.id, step_number=step.step_number).first()
                if not step_res:
                    step_res = TestStepResult(assignment_id=assignment.id, step_number=step.step_number)
                    db.session.add(step_res)
                
                step_res.status = s_status
                step_res.comment = s_comment
                
            db.session.commit()
            flash('Result saved.')
            return redirect(url_for('execute_run', run_id=run.id))

    return render_template(
        'execute.html', 
        run=run, 
        assignments=assignments, 
        stats=stats, 
        state_active=STATE_ACTIVE, 
        state_aborted=STATE_ABORTED, 
        state_finished=STATE_FINISHED, 
        state_created=STATE_CREATED,
        not_tested=RESULT_NOT_TESTED, 
        blocked=RESULT_BLOCKED, 
        failed=RESULT_FAILED,
        ok=RESULT_OK
    )
