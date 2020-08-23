import os

from course_monitor.courses_manager import add_course_job, remove_courses, remove_course, init_monitor, get_time, \
    add_course
from flask import Flask, send_from_directory, Response
from dotenv import load_dotenv

from course_monitor import course_monitor, course

CourseEncoder = course.CourseEncoder
Course = course.Course

API = '/api/v1'

app = Flask(__name__, static_folder="client/build", static_url_path="")

courses = {}
emitters = []
scheduler = None
start_time, end_time, wait_time, jitter = None, None, 180, 10


@app.route(API)
def api_home():
    return 'Welcome to UT Course Monitor API'


@app.route(API + '/courses', methods=['GET'])
def get_courses():
    return Response(
        mimetype="application/json",
        response=CourseEncoder().encode(list(courses.values())),
        status=200
    )


@app.route(API + '/courses', methods=['DELETE'])
def remove_all_courses():
    remove_courses(courses)
    return Response(
        mimetype="plain/text",
        response="successfully removed all courses",
        status=200
    )


@app.route(API + '/course/<uid>', methods=['GET'])
def get_course(uid: str):
    if not Course.valid_uid(uid) or uid not in courses:
        return Response(
            mimetype="text/plain",
            response="course id {} not found or invalid".format(uid),
            status=500
        )

    return Response(
        mimetype="application/json",
        response=CourseEncoder().encode(courses),
        status=200
    )


@app.route(API + '/course/<uid>', methods=['POST'])
def create_course(uid: str):
    if not Course.valid_uid(uid) or uid in courses:
        return Response(
            mimetype="text/plain",
            response="course id {} not valid or already exists".format(uid),
            status=500
        )
    course = add_course(uid, emitters, courses)
    add_course_job(scheduler, course, (start_time, end_time, wait_time), jitter)
    return Response(
        mimetype="text/plain",
        response="course id {} successfully added".format(uid),
        status=200
    )


@app.route(API + '/course/<uid>', methods=['DELETE'])
def remove_course_id(uid: str):
    if not Course.valid_uid(uid) or uid not in courses:
        return Response(
            mimetype="text/plain",
            response="course id {} not valid or not found".format(uid),
            status=500
        )

    remove_course(uid, courses)
    return Response(
        mimetype="text/plain",
        response="course id {} successfully removed".format(uid),
        status=200
    )


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve(path):
    if os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)


if __name__ == '__main__':
    load_dotenv()

    scheduler, emitters = init_monitor(os.getenv('SEM'),
                                       os.getenv('EID'),
                                       os.getenv('UT_PASS'),
                                       True)

    start_time, end_time = get_time(os.getenv('START')), get_time(os.getenv('END'))

    course_monitor.debug = True
    course.debug = True
    wait_time = 180
    jitter = 10

    scheduler.start()
    app.run()
