import os

from dotenv import load_dotenv
from flask import Flask, send_from_directory, Response, request, redirect
from flask_login import LoginManager, login_required, login_user, current_user

from course_monitor import Monitor, CourseEncoder, JobState, set_debug
from course_monitor.utils import \
    add_course_job, remove_course, init_monitor, get_time, add_course, build_sem_code, valid_uid
from models import User

API = '/api/v1'

load_dotenv()
app = Flask(__name__, static_folder='client/build', static_url_path='')
app.secret_key = os.getenv('SECRET_KEY')
login_manager = LoginManager(app)
login_manager.login_view = '/login'

users = {}
courses = {}

usr_name, passwd = os.getenv('EID'), os.getenv('UT_PASS')
scheduler, emitters = init_monitor(os.getenv('SEM'),
                                   os.getenv('EID'),
                                   os.getenv('UT_PASS'),
                                   os.getenv('FLASK_ENV') != 'development')

start_time, end_time = get_time(os.getenv('START')), get_time(os.getenv('END'))
users[usr_name] = User(usr_name, passwd)
wait_time, jitter = 180, 10
set_debug(os.getenv('FLASK_ENV') == 'development')


def invalid_resp(uid: str):
    if not valid_uid(uid):
        return 'course id {} not valid'.format(uid), 400


def undetected_resp(uid: str):
    if not valid_uid(uid) or uid not in courses:
        return 'course id {} not valid or not found'.format(uid), 404


@app.route(API)
def api_home():
    return 'UT Course Monitor API'


@app.route(API + '/config', methods=['GET', 'POST'])
@login_required
def config():
    global wait_time, start_time, end_time

    if request.method == 'POST':
        if request.values.sid:
            Monitor.sid = build_sem_code(request.values.sid)

        # todo do proper precondition checking
        if request.values.interval:
            wait_time = int(request.values.interval)
            pass  # todo implement
        if t := request.values.start:
            start_time = get_time(t)
        if t := request.values.end:
            end_time = get_time(t)

    return {'sid': str(Monitor.sid),
            'interval': str(wait_time),
            'start': start_time.strftime('%H:%M'),
            'end': end_time.strftime('%H:%M')}


@app.route(API + '/courses', methods=['GET'])
@login_required
def get_courses():
    return Response(
        mimetype='application/json',
        response=CourseEncoder().encode(list(courses.values())))


@app.route(API + '/courses/<uid>', methods=['GET'])
@login_required
def get_course(uid: str):
    if resp := undetected_resp(uid):
        return resp

    return Response(
        mimetype='application/json',
        response=CourseEncoder().encode(courses))


@app.route(API + '/courses/<uid>', methods=['POST'])
@login_required
def create_course(uid: str):
    if resp := invalid_resp(uid):
        return resp

    course = add_course(uid, emitters, courses)
    add_course_job(scheduler, course, (start_time, end_time, wait_time), jitter)
    return 'course id {} successfully added'.format(uid), 201


@app.route(API + '/courses/<uid>', methods=['DELETE'])
@login_required
def remove_course_id(uid: str):
    if resp := undetected_resp(uid):
        return resp

    remove_course(uid, courses)
    return 'course id {} successfully removed'.format(uid)


@app.route(API + '/courses/<uid>/pause', methods=['POST'])
@login_required
def pause_course(uid: str):
    if resp := undetected_resp(uid):
        return resp

    course = courses[uid]
    if request.values['status'] == 'true':
        course.pause_job()
    if request.values['status'] == 'false':
        course.resume_job()

    return {'status': course.paused}


@app.route(API + '/login_status', methods=['GET'])
def login_status():

    if not current_user.is_authenticated:
        return {'user': False}

    browser_logged_in = Monitor.logged_in() and not Monitor.login_fail
    return {'browser': browser_logged_in,
            'user': current_user.is_authenticated}


@app.route(API + '/browser_login', methods=['POST'])
@login_required
def browser_login_action():
    scheduler.add_job(Monitor.login, id=str(Monitor.sid))
    login_state = JobState(str(Monitor.sid))
    login_state.listen_done(scheduler)
    login_state.wait_done()
    return {'status': Monitor.logged_in()}


@login_manager.user_loader
def load_user(user_id):
    return users[user_id]


@app.route('/login', methods=['GET'])
def login_view():
    if current_user.is_authenticated:
        return redirect('/')
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')

    user_id = request.form.get('id')
    passwd = request.form.get('password')

    user = users[user_id]
    if not user or not user.check_password(passwd):
        return 'fail', 401

    login_user(user, remember=True)
    return 'success'


@app.route('/', defaults={'path': ''})
@app.route("/<path>")
@login_required
def index(path):
    return send_from_directory(app.static_folder, 'index.html')


scheduler.start()
if __name__ == '__main__':
    app.run(use_reloader=False)
