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


def create_courses(uids, emitters) -> []:
    courses = []
    for uid in uids:
        courses.append(Course(uid, emitters))
    return courses


def add_courses_to_jobs(scheduler, courses: [Course], wait_time) -> []:
    jobs = []
    for course in courses:
        jobs.append(scheduler.add_job(course.do_check,
                                      'interval',
                                      seconds=wait_time,
                                      next_run_time=datetime.now(),
                                      misfire_grace_time=wait_time,
                                      coalesce=True))
    return jobs


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

    uids = [str(uid) for uid in args.uids]
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
    jobs = add_courses_to_jobs(scheduler, courses, wait_time)
    scheduler.start()

    while True:
        time.sleep(5)  # todo use this space to allow command parsing
