import os
import argparse
from datetime import datetime

from dotenv import load_dotenv
from selenium import webdriver

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

import course_monitor
from notification_emitter import SlackEmitter, ConsoleEmitter

CourseMonitor = course_monitor.CourseMonitor
Course = course_monitor.Course


def sem_code_builder(sem: str):
    semester_pts = sem.lower().split()
    if len(semester_pts) != 2 or not semester_pts[1].isnumeric():
        raise Exception('Given semester {} is wrong'.format(sem))

    season_codes = {'fall': 9, 'spring': 2, 'summer': 6}
    year = int(semester_pts[1])
    season_code = season_codes[semester_pts[0]]
    return '{}{}'.format(year, season_code)


def init_browser(headless=False):
    options = webdriver.ChromeOptions()
    options.headless = headless

    return webdriver.Chrome(options=options)


def add_courses(uids: [int], emitters: []) -> {}:
    courses = {}
    for uid in uids:
        courses[uid] = Course(uid, emitters)
    return courses


def add_courses_to_jobs(scheduler: BackgroundScheduler, courses: {}, times: tuple, jitter=0) -> []:
    for course in courses.values():
        add_course_job(scheduler, course, times, jitter)


def add_course_job(scheduler: BackgroundScheduler, course: Course, times: tuple, jitter=0):
    def get_today_times(start_time, end_time):
        return datetime.combine(datetime.now(), start_time), datetime.combine(datetime.now(), end_time)

    start_time, end_time, wait_time = times
    # noinspection PyTypeChecker
    job = scheduler.add_job(course.check,
                            'interval',
                            seconds=wait_time,
                            next_run_time=datetime.now(),
                            misfire_grace_time=None,
                            id=str(course.uid),
                            jitter=jitter,
                            coalesce=True)

    if start_time and end_time:
        start_date, end_date = get_today_times(start_time, end_time)
        scheduler.add_job(remove_course_job, args=(course,), trigger='date', next_run_time=end_date)
        scheduler.add_job(add_course_job, args=(scheduler, course, times, jitter), next_run_time=start_date)

    course.job = job
    return job


def remove_courses(courses: {}):
    for uid in courses:
        remove_course(uid)


def remove_course(uid: int):
    with courses.pop(uid) as c:
        remove_course_job(c)


def remove_courses_from_jobs(courses: {}):
    for course in courses.values():
        remove_course_job(course)


def remove_course_job(course: Course):
    if course.job:
        course.job.remove()


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--sem', '-s',
                        metavar='semester',
                        type=str,
                        required=False,
                        help='Semester of course schedule to look in')

    parser.add_argument('--uids', '-u',
                        metavar='id',
                        type=int,
                        nargs="*",
                        default=[],
                        required=False,
                        help='space separated list of course unique IDs we are interested in searching')

    parser.add_argument('--period', '-p',
                        type=int,
                        default=180,
                        required=False,
                        help='time spent between requests in seconds (180 by default)')

    parser.add_argument('--headless',
                        default=False,
                        required=False,
                        action='store_true',
                        help='add this flag to run Chrome in headless mode (no GUI available)')

    parser.add_argument('--verbose', '-v',
                        default=False,
                        required=False,
                        action='store_true',
                        help='add this flag to show extra print statements in cmd')

    parser.add_argument('--randomize', '-r',
                        default=0,
                        const=10,
                        required=False,
                        action='store_const',
                        help='add this flag to randomize the course request times (10s by default)')


def build_emitters(sem_id: str) -> []:
    emitters = [ConsoleEmitter()]
    token, channel = os.getenv('SLACK_TOKEN'), os.getenv('SLACK_CHANNEL')
    if token and channel:
        emitters.append(SlackEmitter(sem_id, token, channel))

    return emitters


def parse_input(cmd):
    tokens = cmd.split()
    cmd = tokens[0].lower()

    if cmd == 'list':
        print('list of courses currently being run for')
        for uid in courses:
            print('- {}'.format(courses[uid]))

    elif cmd == 'clear':
        remove_courses(courses)
        print('cleared all courses')

    elif cmd == 'add':
        if not len(tokens) == 2:
            print('error, invalid input')
        else:
            uid = int(tokens[1])
            if uid in courses:
                return
            course = Course(uid, emitters)
            courses[uid] = course
            add_course_job(scheduler, course, (start_time, end_time, wait_time), jitter)
            print('added {}'.format(uid))
    elif cmd == 'remove':
        if not len(tokens) == 2:
            print('error, invalid input')
        else:
            uid = int(tokens[1])
            if uid not in courses:
                return
            remove_course(uid)
            print('removed {}'.format(uid))
    elif cmd == 'exit':
        exit()
    else:
        print('unknown command')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Monitor UT Course Schedule',
        allow_abbrev=True)
    add_args(parser)
    args = parser.parse_args()

    load_dotenv()

    uids = [uid for uid in args.uids]
    usr_name, passwd = (os.getenv('EID'), os.getenv('UT_PASS'))
    browser = init_browser(args.headless)

    sid = sem_code_builder(args.sem or os.getenv('SEM'))
    emitters = build_emitters(sid)

    start_time, end_time = None, None
    if os.getenv('START') and os.getenv('END'):
        start_time = datetime.strptime(os.getenv('START'), "%H%M").time()
        end_time = datetime.strptime(os.getenv('END'), "%H%M").time()

    wait_time = int(args.period)
    course_monitor.debug = args.verbose

    CourseMonitor.browser = browser
    CourseMonitor.sid = sid
    CourseMonitor.usr_name = usr_name
    CourseMonitor.passwd = passwd

    jitter = args.randomize
    courses = add_courses(uids, emitters)
    # CourseMonitor.login(sid)  # login pre-emptively before getting all course information

    scheduler = BackgroundScheduler(daemon=True, executors={'default': ThreadPoolExecutor(1)})
    scheduler.add_job(CourseMonitor.login, args=(sid,), id=str(sid))
    add_courses_to_jobs(scheduler, courses, (start_time, end_time, wait_time), jitter)
    scheduler.start()

    while True:
        parse_input(input())
