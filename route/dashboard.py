from flask import render_template
from flask_login import current_user
from model.project import Project, STATE_ACTIVE, STATE_CREATED

# ROUTE: Dashboard, default route
def route_dashboard():
    all_projects = Project.query.all()
    my_runs = {}

    for project in all_projects:
        my_runs |= project.get_open_runs(current_user)

    if current_user.is_admin():
        return render_template(
            'dashboard.html', 
            my_projects=all_projects, 
            my_runs=my_runs, 
            state_created=STATE_CREATED, 
            state_active=STATE_ACTIVE
        )
    
    if current_user.is_test_manager():
        my_projects = Project.query.filter_by(owner_id=current_user.id).all()
        return render_template('dashboard.html', 
            my_projects=my_projects, 
            my_runs=my_runs, 
            state_created=STATE_CREATED, 
            state_active=STATE_ACTIVE
        )

    return render_template('dashboard.html', my_runs=my_runs, state_created=STATE_CREATED, state_active=STATE_ACTIVE)
