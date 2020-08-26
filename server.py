import os

from dotenv import load_dotenv
from flask import Flask, send_from_directory, Response, request, redirect, jsonify
from flask_login import LoginManager, login_required, login_user, current_user

from course_monitor import course_monitor, course, JobState
from course_monitor.courses_manager import \
    add_course_job, remove_courses, remove_course, init_monitor, get_time, add_course
from models import User

CourseMonitor = course_monitor.CourseMonitor
CourseEncoder = course.CourseEncoder
Course = course.Course

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
course_monitor.debug = True
course.debug = True


@app.route(API)
def api_home():
    return 'Welcome to UT Course Monitor API'


@app.route(API + '/sid', methods=['GET'])
@login_required
def get_sid():
    return Response(
        mimetype='text/plain',
        response=str(CourseMonitor.sid),
        status=200,
    )


@app.route(API + '/courses', methods=['GET'])
@login_required
def get_courses():
    return Response(
        mimetype='application/json',
        response=CourseEncoder().encode(list(courses.values())),
        status=200,
    )


@app.route(API + '/courses', methods=['DELETE'])
@login_required
def remove_all_courses():
    remove_courses(courses)
    return Response(
        mimetype='plain/text',
        response='successfully removed all courses',
        status=200,
    )


@app.route(API + '/course/<uid>', methods=['GET'])
@login_required
def get_course(uid: str):
    if not Course.valid_uid(uid) or uid not in courses:
        return Response(
            mimetype='text/plain',
            response='course id {} not found or invalid'.format(uid),
            status=400 if Course.valid_uid(uid) else 404,
        )

    return Response(
        mimetype='application/json',
        response=CourseEncoder().encode(courses),
        status=200,
    )


@app.route(API + '/course/<uid>', methods=['POST'])
@login_required
def create_course(uid: str):
    if not Course.valid_uid(uid) or uid in courses:
        return Response(
            mimetype='text/plain',
            response='course id {} not valid or already exists'.format(uid),
            status=400 if Course.valid_uid(uid) else 404,
        )
    course = add_course(uid, emitters, courses)
    add_course_job(scheduler, course, (start_time, end_time, wait_time), jitter)
    return Response(
        mimetype='text/plain',
        response='course id {} successfully added'.format(uid),
        status=201,
    )


@app.route(API + '/course/<uid>', methods=['DELETE'])
@login_required
def remove_course_id(uid: str):
    if not Course.valid_uid(uid) or uid not in courses:
        return Response(
            mimetype='text/plain',
            response='course id {} not valid or not found'.format(uid),
            status=400 if Course.valid_uid(uid) else 404,
        )

    remove_course(uid, courses)
    return Response(
        mimetype='text/plain',
        response='course id {} successfully removed'.format(uid),
        status=200,
    )


@app.route(API + '/logged_in', methods=['GET'])
def browser_login_status():
    browser_logged_in = CourseMonitor.logged_in() and not CourseMonitor.login_fail
    return jsonify({'status': browser_logged_in})


@app.route(API + '/logged_in', methods=['POST'])
def browser_login_action():
    scheduler.add_job(CourseMonitor.login, id=str(CourseMonitor.sid))
    login_state = JobState(str(CourseMonitor.sid))
    login_state.listen_done(scheduler)
    login_state.wait_done()
    return jsonify({'status': CourseMonitor.logged_in()})


@login_manager.user_loader
def load_user(user_id):
    return users[user_id]


@app.route(API + '/login_status', methods=['GET'])
def is_logged_in():
    return jsonify({'status': current_user.is_authenticated})


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
        return Response(
            mimetype='text/plain',
            response='fail',
            status=501,
        )

    login_user(user, remember=True)
    return Response(
        mimetype='text/plain',
        response='success',
        status=200,
    )


@app.route('/', defaults={'path': ''})
@app.route("/<path>")
@login_required
def index(path):
    return send_from_directory(app.static_folder, 'index.html')


scheduler.start()
if __name__ == '__main__':
    app.run(use_reloader=False)
