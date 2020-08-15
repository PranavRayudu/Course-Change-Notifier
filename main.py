import os
import time
import argparse
from datetime import datetime

from dotenv import load_dotenv
from selenium import webdriver

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.interval import IntervalTrigger
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


def create_courses(uids: [int], emitters: []) -> {}:
    courses = {}
    for uid in uids:
        courses[uid] = Course(uid, emitters)
    return courses


def build_trigger(times: tuple):
    start_time, end_time, wait_time = times

    if start_time and end_time:
        if start_time.hour == end_time.hour:
            hours = [CronTrigger(hour=start_time.hour,
                                 minute="{}-{}".format(start_time.minute, end_time.minute),
                                 second="*/{}".format(wait_time))]
        else:
            hours = [
                CronTrigger(hour=start_time.hour, minute="{}-59".format(start_time.minute),
                            second="*/{}".format(wait_time)),
                CronTrigger(hour=end_time.hour, minute="0-{}".format(end_time.minute),
                            second="*/{}".format(wait_time))
            ]
            if start_time.hour + 1 < end_time.hour:
                hours.append(CronTrigger(hour="{}-{}".format(start_time.hour + 1, end_time.hour - 1),
                                         minute="0-59",
                                         second="*/{}".format(wait_time)))
    else:
        hours = [IntervalTrigger(seconds=wait_time)]

    return OrTrigger(hours)


def add_course_job(scheduler: BackgroundScheduler, course: Course, times: tuple):
    _, _, wait_time = times

    job = scheduler.add_job(course.check,
                            build_trigger(times),
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


def add_courses_to_jobs(scheduler: BackgroundScheduler, courses: {}, times: tuple) -> []:
    for course in courses.values():
        add_course_job(scheduler, course, times)


def clear_course_jobs(courses: {}):
    for uid in courses:
        remove_course_job(uid)


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
                        help='time spent between requests (s); Default 180')

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


def parse_input(cmd):
    tokens = cmd.split()
    cmd = tokens[0].lower()

    if cmd == 'list':
        print('list of courses currently being run for')
        for uid in courses:
            print('- {}'.format(courses[uid]))

    elif cmd == 'clear':
        clear_course_jobs(courses)
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
            add_course_job(scheduler, course, (start_time, end_time, wait_time))
            print('added {}'.format(uid))
    elif cmd == 'remove':
        if not len(tokens) == 2:
            print('error, invalid input')
        else:
            uid = int(tokens[1])
            if uid not in courses:
                return
            remove_course_job(uid)
            print('removed {}'.format(uid))


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

    start_time = datetime.strptime(os.getenv('START') or '0000', "%H%M").time()
    end_time = datetime.strptime(os.getenv('END') or '2359', "%H%M").time()

    wait_time = int(args.period)

    CourseMonitor.browser = browser
    CourseMonitor.sid = sid
    CourseMonitor.usr_name = usr_name
    CourseMonitor.passwd = passwd

    courses = create_courses(uids, emitters)

    scheduler = BackgroundScheduler(daemon=True, executors={'default': ThreadPoolExecutor(1)})
    scheduler.add_job(CourseMonitor.login, args=(sid,), id=str(sid))
    add_courses_to_jobs(scheduler, courses, (start_time, end_time, wait_time))
    scheduler.start()

    while True:
        parse_input(input())
