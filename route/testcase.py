from utils.database import db
from flask import redirect, url_for, abort, request, render_template, flash
from flask_login import current_user
from model.testcase import TestCase, PRIORITY_HIGH, PRIORITY_LOW, PRIORITY_NORMAL
from model.tag import Tag
from model.project import Project
from model.testcase import TestCase, PRIORITY_NORMAL
from model.step import TestStep
from utils.llm import call_ai_model

DIRECTION_UP = 'up'
DIRECTION_DOWN = 'down'

# ROUTE: New test case, modify test case
def route_testcase_edit(project_id: int, case_id: int|None = None):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_admin() or (current_user.is_test_manager() and project.owner_id == current_user.id)): 
        abort(403)

    if case_id:
        case: TestCase = TestCase.query.get(case_id)
    else:
        case: TestCase = TestCase(project_id=project.id)
        max_seq = db.session.query(db.func.max(TestCase.sequence)).filter_by(project_id=project.id).scalar()
        case.sequence = (max_seq or 0) + 1

    if request.method == 'POST':
        case.sequence = int(request.form.get('sequence', 0))
        case.title = str(request.form.get('title'))
        case.summary = str(request.form.get('summary'))
        case.precondition = str(request.form.get('precondition'))
        case.postcondition = str(request.form.get('postcondition'))
        case.priority = str(request.form.get('priority'))
        case.source = str(request.form.get('source'))
        
        tag_names = [t.strip() for t in request.form.get('tags', '').split(' ') if t.strip()]
        case.tags = []
        for t_name in tag_names:
            tag = Tag.query.filter_by(name=t_name).first()
            if not tag:
                tag = Tag(name=t_name)
                db.session.add(tag)
            case.tags.append(tag)

        case.store()
        
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
    return render_template(
        'case_form.html', 
        project=project, 
        case=case, 
        all_tags=all_tags, 
        prio1=PRIORITY_HIGH, 
        prio2=PRIORITY_NORMAL, 
        prio3=PRIORITY_LOW
    )

# ROUTE: Sort test cases
def route_testcase_sort(case_id: int, direction: str):
    current_case = TestCase.query.get_or_404(case_id)
    project = current_case.project
    
    if not (current_user.is_admin() or (current_user.is_test_manager() and project.owner_id == current_user.id)):
        abort(403)

    sorted_cases = TestCase.query.filter_by(project_id=project.id).order_by(TestCase.sequence.asc(), TestCase.id.asc()).all()
    
    current_index = [i for i, case in enumerate(sorted_cases) if case.id == case_id][0]

    if direction == DIRECTION_UP and current_index > 0:
        prev_case = sorted_cases[current_index - 1]
        temp_sequence = current_case.sequence
        current_case.sequence = prev_case.sequence
        prev_case.sequence = temp_sequence
        
        db.session.commit()
        flash(f'Test case "{current_case.title}" moved up.')
        
    elif direction == DIRECTION_DOWN and current_index < len(sorted_cases) - 1:
        next_case = sorted_cases[current_index + 1]
        temp_sequence = current_case.sequence
        current_case.sequence = next_case.sequence
        next_case.sequence = temp_sequence
        
        db.session.commit()
        flash(f'Test case "{current_case.title}" moved down.')
        
    return redirect(url_for('view_project', project_id=project.id))

# ROUTE: Delete test case, redirected to project
def route_testcase_delete(case_id: int):
    case: TestCase = TestCase.query.get_or_404(case_id)
    if not (current_user.is_admin() or (current_user.is_test_manager() and case.project.owner_id == current_user.id)): 
        abort(403)

    title = case.title
    case.delete()
    flash(f"Deleted test case '{title}'")
    return redirect(url_for('view_project', project_id=case.project_id))

# ROUTE: Wizard for AI supported test case generation
def route_testcase_ai_prepare(project_id: int):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_admin() or (current_user.is_test_manager() and project.owner_id == current_user.id)): 
        abort(403)
        
    return render_template('case_ai_form.html', project=project)

# ROUTE: Store AI generated test cases
def route_testcase_ai_gen(project_id: int, host: str, key: str, model: str):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_admin() or (current_user.is_test_manager() and project.owner_id == current_user.id)): 
        abort(403)
        
    requirement_text = request.form.get('requirement', '')
    
    if not requirement_text.strip():
        flash('Error: Requirement text is empty.', 'error')
        return redirect(url_for('create_case_ai_form', project_id=project.id))

    try:
        generated_cases_data = call_ai_model(requirement_text, host, key, model)
    except Exception as e:
        flash(f"Error: AI model returned an invalid response: {e}", "error")
        return redirect(url_for('create_case_ai_form', project_id=project.id))
    
    if generated_cases_data is None:
        flash('Error: Could not connect to AI model.', 'error')
        return redirect(url_for('create_case_ai_form', project_id=project.id))

    num_created = 0
    
    for case_data in generated_cases_data:
        max_seq = db.session.query(db.func.max(TestCase.sequence)).filter_by(project_id=project.id).scalar()
        
        tags = []
        my_tags = [t.strip() for t in case_data.get('tags', '').split(' ') if t.strip()]
        my_tags.append("#gen-ai")

        for my_tag in my_tags:
            tag = Tag.query.filter_by(name=my_tag).first()
            if not tag:
                tag = Tag(name=my_tag)
                tag.store()
            tags.append(tag)
            
        new_case = TestCase(
            project_id=project.id,
            sequence=(max_seq or 0) + 1,
            title=case_data.get('title', 'Generated Test Case'),
            summary=case_data.get('summary'),
            precondition=case_data.get('precondition'),
            postcondition=case_data.get('postcondition'),
            priority=case_data.get('priority', PRIORITY_NORMAL),
            source=case_data.get('source'),
            tags=tags
        )
        new_case.store()
        
        steps_data = case_data.get('steps', [])
        for idx, step_data in enumerate(steps_data):
            step = TestStep(
                test_case_id=new_case.id,
                step_number=idx + 1,
                action=step_data.get('action', ''),
                expected_result=step_data.get('expected_result', '')
            )
            db.session.add(step)
            
        db.session.commit()
        num_created += 1

    flash(f"{num_created} test cases successfully generated and added to the current project. All generated test cases have been marked with tag #gen-ai automatically.")
    return redirect(url_for('view_project', project_id=project.id))
