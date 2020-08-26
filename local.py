#!/usr/bin/env python

import os
import argparse

from dotenv import load_dotenv

from course_monitor import Monitor, set_debug
from course_monitor.utils import add_courses, add_courses_to_jobs, add_course_job, remove_courses, \
    remove_course, init_monitor, get_time, add_course, valid_uid


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


def parse_input(cmd) -> None:
    tokens = cmd.split()
    cmd = tokens[0].lower()

    if cmd == 'list':
        print('list of courses being checked')
        for uid in courses:
            print('- {}'.format(courses[uid]))
        scheduler.print_jobs()
    elif cmd == 'clear':
        remove_courses(courses)
        print('cleared all courses')
    elif cmd == 'login':
        scheduler.add_job(Monitor.login, id=str(Monitor.sid))
    elif cmd == 'exit':
        exit()

    if not len(tokens) == 2:
        print('error, invalid input')
        return

    uid = tokens[1]

    if not valid_uid(uid):
        print('invalid uid')
        return

    course = courses[uid]

    if cmd == 'add':
        course = add_course(uid, emitters, courses)
        add_course_job(scheduler, course, (start_time, end_time, wait_time), jitter)
        print('added {}'.format(uid))
    elif cmd == 'remove':
        remove_course(uid, courses)
        print('removed {}'.format(uid))
    elif cmd == 'pause':
        course.resume_job()
    elif cmd == 'resume':
        course = courses[uid]
        course.pause_job(course)
    else:
        print('unknown command')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Monitor UT Course Schedule',
        allow_abbrev=True)
    add_args(parser)
    args = parser.parse_args()

    load_dotenv()

    uids = [uid for uid in args.uids if valid_uid(uid)]

    scheduler, emitters = init_monitor(args.sem or os.getenv('SEM'),
                                       os.getenv('EID'),
                                       os.getenv('UT_PASS'),
                                       args.headless)

    start_time, end_time = get_time(os.getenv('START')), get_time(os.getenv('END'))

    wait_time = int(args.period)

    set_debug(args.verbose)

    jitter = args.randomize
    courses = add_courses(uids, emitters)
    add_courses_to_jobs(scheduler, courses, (start_time, end_time, wait_time), jitter)
    scheduler.start()

    while True:
        parse_input(input())
