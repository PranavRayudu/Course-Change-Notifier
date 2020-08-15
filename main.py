import os
import time
import argparse
from datetime import datetime

from dotenv import load_dotenv
from selenium import webdriver

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from course_monitor import CourseMonitor, Course
from notification_emitter import SlackEmitter, ConsoleEmitter


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


def create_courses(uids, emitters) -> {}:
    courses = {}
    for uid in uids:
        courses[uid] = Course(uid, emitters)
    return courses


def add_course_job(scheduler, course: Course, wait_time: int):
    job = scheduler.add_job(course.do_check,
                            'interval',
                            seconds=wait_time,
                            next_run_time=datetime.now(),
                            misfire_grace_time=wait_time,
                            id=str(course.uid),
                            coalesce=True)
    course.job = job
    return job


def remove_course_job(uid: int):
    with courses.pop(uid) as c:
        if c.job:
            c.job.remove()


def add_courses_to_jobs(scheduler, courses: {}, wait_time: int) -> []:
    for course in courses.values():
        add_course_job(scheduler, course, wait_time)


def add_args(parser) -> None:
    parser.add_argument('--sem', '-s',
                        metavar='semester',
                        type=str,
                        required=True,
                        help='Semester of course schedule to look in')

    parser.add_argument('--uids', '-u',
                        metavar='id',
                        type=int,
                        nargs="+",
                        default=[],
                        required=True,
                        help='space separated list of course unique IDs we are interested in searching')

    parser.add_argument('--period', '-p',
                        type=int,
                        default=180,
                        required=False,
                        help='time spent between requests (s)')

    parser.add_argument('--headless',
                        default=False,
                        required=False,
                        action='store_true',
                        help='add this flag to run Chrome in headless mode (no GUI available)')


def build_emitters(sem_id: str) -> []:
    emitters = [ConsoleEmitter()]
    token, channel = os.getenv('SLACK_TOKEN'), os.getenv('SLACK_CHANNEL')
    if token and channel:
        emitters.append(SlackEmitter(sem_id, token, channel))

    return emitters


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Monitor UT Course Schedule',
        allow_abbrev=True)
    add_args(parser)
    args = parser.parse_args()

    load_dotenv(os.path.join('./', '.env'))

    uids = [uid for uid in args.uids]
    usr_name, passwd = (os.getenv('EID'), os.getenv('UT_PASS'))
    browser = init_browser(args.headless)

    sid = sem_code_builder(args.sem)
    emitters = build_emitters(sid)
    wait_time = int(args.period)

    CourseMonitor.browser = browser
    CourseMonitor.sid = sid
    CourseMonitor.usr_name = usr_name
    CourseMonitor.passwd = passwd

    courses = create_courses(uids, emitters)

    scheduler = BackgroundScheduler(daemon=True, executors={'default': ThreadPoolExecutor(1)})
    add_courses_to_jobs(scheduler, courses, wait_time)
    scheduler.start()

    while True:
        cmd = input()
        tokens = cmd.split()
        cmd = tokens[0].lower()

        if cmd == 'list':
            print('list of courses currently being run for')
            for uid in courses:
                course = courses[uid]
                if course.cur_course:
                    print('- {}: {} ({})'.format(course.cur_course[0], course.cur_course[1], course.uid))
                else:
                    print('- {}'.format(course.uid))

        elif cmd == 'clear':
            for uid in courses:
                remove_course_job(uid)
            print('cleared all courses')

        elif cmd == 'add':
            if not len(tokens) == 2:
                print('error, invalid input')
            else:
                uid = int(tokens[1])
                if uid in courses:
                    continue
                course = Course(uid, emitters)
                courses[uid] = course
                add_course_job(scheduler, course, wait_time)
                print('added {}'.format(uid))
        elif cmd == 'remove':
            if not len(tokens) == 2:
                print('error, invalid input')
            else:
                uid = int(tokens[1])
                if uid not in courses:
                    continue
                remove_course_job(uid)
                print('removed {}'.format(uid))
