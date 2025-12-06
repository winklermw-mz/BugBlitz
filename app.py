import os
from utils.database import setup_database, setup_login_manager
from flask import Flask
from flask_login import login_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dein-geheimer-schluessel-hier'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bugblitz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = setup_database(app)
login_manager = setup_login_manager(app)

LLM_HOST = os.getenv("LLM_HOST", "http://localhost:1234/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "lm-studio")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen3-vl-4b")

from model.user import User
from utils.init import create_initial_data
from route.login import route_login
from route.logout import route_logout
from route.dashboard import route_dashboard
from route.user import route_user_administration, route_user_edit
from route.project import route_project_create, route_project_delete, route_project_view
from route.testcase import route_testcase_delete, route_testcase_edit, route_testcase_sort, route_testcase_ai_prepare, route_testcase_ai_gen
from route.run import route_run_edit, route_run_create, route_run_update, route_run_update_state, route_run_execute


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def dashboard():
    return route_dashboard()

@app.route('/login', methods=['GET', 'POST'])
def login():
    return route_login()

@app.route('/logout')
@login_required
def logout():
    return route_logout()

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    return route_user_administration()

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id: int):
    return route_user_edit(user_id)

@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def create_project():
    return route_project_create()

@app.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id: int):
    return route_project_delete(project_id)

@app.route('/project/<int:project_id>')
@login_required
def view_project(project_id: int):
    return route_project_view(project_id)

@app.route('/project/<int:project_id>/case/new', methods=['GET', 'POST'])
@app.route('/project/<int:project_id>/case/<int:case_id>/edit', methods=['GET', 'POST'])
@login_required
def manage_case(project_id: int , case_id: int|None = None):
    return route_testcase_edit(project_id, case_id)

@app.route('/case/<int:case_id>/delete', methods=['POST'])
@login_required
def delete_case(case_id: int):
    return route_testcase_delete(case_id)

@app.route('/case/<int:case_id>/sort/<direction>', methods=['POST'])
@login_required
def sort_case(case_id: int, direction: str):
    return route_testcase_sort(case_id, direction)

@app.route('/project/<int:project_id>/case/ai')
@login_required
def create_case_ai_form(project_id: int):
    return route_testcase_ai_prepare(project_id)

@app.route('/project/<int:project_id>/case/ai/extract', methods=['POST'])
@login_required
def extract_case_ai(project_id: int):
    return route_testcase_ai_gen(project_id, LLM_HOST, LLM_API_KEY, LLM_MODEL)

@app.route('/project/<int:project_id>/run/new', methods=['GET', 'POST'])
@login_required
def create_run(project_id: int):
    return route_run_create(project_id)

@app.route('/run/<int:run_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_run(run_id: int):
    return route_run_edit(run_id)

@app.route('/run/<int:run_id>/update', methods=['POST'])
@login_required
def update_run(run_id: int):
    return route_run_update(run_id)

@app.route('/run/<int:run_id>/status', methods=['POST'])
@login_required
def update_run_status(run_id: int):
    return route_run_update_state(run_id)

@app.route('/run/<int:run_id>/execute', methods=['GET', 'POST'])
@login_required
def execute_run(run_id: int):
    return route_run_execute(run_id)


if __name__ == '__main__':
    create_initial_data(app)
    app.run(host="0.0.0.0", port=8100, debug=True)
