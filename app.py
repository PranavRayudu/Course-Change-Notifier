import os

from main import init_monitor, get_start_end, add_course_job, remove_course, remove_courses
from flask import Flask, send_from_directory, Response
from dotenv import load_dotenv

from course_monitor import course_monitor, course

CourseEncoder = course.CourseEncoder
Course = course.Course

app = Flask(__name__, static_folder="client/build", static_url_path="")
API = '/api/v1'

courses = {}


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
    course = Course(uid, emitters)
    courses[uid] = course
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

    usr_name, passwd = (os.getenv('EID'), os.getenv('UT_PASS'))

    scheduler, emitters = init_monitor(os.getenv('SEM'),
                                       usr_name, passwd, True)

    start_time, end_time = get_start_end(os.getenv('START'), os.getenv('END'))

    course_monitor.debug = True
    course.debug = True
    wait_time = 180
    jitter = 10

    scheduler.start()
    app.run()