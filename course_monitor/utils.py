import os
from datetime import datetime, timedelta, time

from selenium import webdriver
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from course_monitor import Course, Monitor, ConsoleEmitter, SlackEmitter


def build_sem_code(sem: str):
    semester_pts = sem.lower().split()
    if len(semester_pts) != 2 or not semester_pts[1].isnumeric():
        raise Exception('Given semester {} is wrong'.format(sem))

    season_codes = {'fall': 9, 'spring': 2, 'summer': 6}
    year = int(semester_pts[1])
    season_code = season_codes[semester_pts[0]]
    if not season_code:
        raise Exception('Given semester {} is wrong'.format(sem))
    return '{}{}'.format(year, season_code)


def init_browser(headless=False):
    options = webdriver.ChromeOptions()
    options.headless = headless

    if os.getenv('FLASK_ENV') == 'production':
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

    if os.getenv('GOOGLE_CHROME_BIN'):
        options.binary_location = os.getenv('GOOGLE_CHROME_BIN')
    if os.getenv('CHROMEDRIVER_PATH'):
        return webdriver.Chrome(os.getenv('CHROMEDRIVER_PATH'), options=options)
    return webdriver.Chrome(options=options)


def add_course(uid: str, emitters: [], courses: {}):
    if uid not in courses:
        course = Course(uid, emitters)
        courses[uid] = course
        return course


def add_courses(uids: [str], emitters: []) -> {}:
    courses = {}
    for uid in uids:
        add_course(uid, emitters, courses)
    return courses


def add_courses_to_jobs(scheduler: BackgroundScheduler, courses: {}, times: (None, None, 180), jitter=0) -> []:
    for course in courses.values():
        add_course_job(scheduler, course, times, jitter)


def add_course_job(scheduler: BackgroundScheduler, course: Course, times: tuple, jitter=0):
    def get_course_job_ids(uid: str):
        # job ids: <uid>-c (course check), <uid>-s (start course check), <uid>-e (end course check)
        return '{}-c'.format(uid), '{}-s'.format(uid), '{}-e'.format(uid)

    def is_time_between(begin_time=None, end_time=None):

        if begin_time and end_time:
            check_time = datetime.now().time()
            if begin_time < end_time:
                return begin_time <= check_time <= end_time
            else:  # crosses midnight
                return check_time >= begin_time or check_time <= end_time
        return True

    def next_datetime(time: time) -> datetime:
        current = datetime.now()
        repl = datetime.combine(current, time)
        while repl <= current:
            repl = repl + timedelta(days=1)
        return repl

    course_check_id, course_start_id, course_end_id = get_course_job_ids(course.uid)
    start_time, end_time, wait_time = times

    if is_time_between(start_time, end_time):
        # noinspection PyTypeChecker
        course.job = scheduler.add_job(
            course.check,
            'interval',
            seconds=wait_time,
            next_run_time=datetime.now(),
            misfire_grace_time=None,
            id=course_check_id,
            jitter=jitter,
            coalesce=True)
        if course.paused:
            course.job.pause()

    if start_time and end_time:
        # start_date, end_date = get_today_times(start_time, end_time)
        start_date, end_date = next_datetime(start_time), next_datetime(end_time)
        course.start_job = scheduler.add_job(
            add_course_job,
            trigger='date',
            args=(scheduler, course, times, jitter),
            id=course_start_id,
            run_date=start_date)
        course.end_job = scheduler.add_job(
            remove_course_job,
            args=(course,),
            trigger='date',
            id=course_end_id,
            run_date=end_date)
    return course.job


def remove_courses(courses: {}):
    for uid in list(courses.keys()):
        remove_course(uid, courses)


def remove_course(uid: str, courses: {}) -> Course:
    course = None
    if uid in courses:
        remove_course_job(course := courses.pop(uid))
    return course


def remove_courses_from_jobs(courses: {}):
    for course in courses.values():
        remove_course_job(course)


def remove_course_job(course: Course):
    course.remove_job()


def build_emitters(sem_id: str) -> []:
    emitters = [ConsoleEmitter()]
    token, channel = os.getenv('SLACK_TOKEN'), os.getenv('SLACK_CHANNEL')
    if token and channel:
        emitters.append(SlackEmitter(sem_id, token, channel))

    return emitters


def init_monitor(sem, usr_name, passwd, headless=False):
    browser = init_browser(headless)

    sid = build_sem_code(sem)
    emitters = build_emitters(sid)

    Monitor.browser = browser
    Monitor.sid = sid
    Monitor.usr_name = usr_name
    Monitor.passwd = passwd

    scheduler = BackgroundScheduler(daemon=True, executors={'default': ThreadPoolExecutor(1)})
    # scheduler.add_job(CourseMonitor.login, id=str(sid))
    # CourseMonitor.login()  # login pre-emptively before getting all course information

    return scheduler, emitters


def get_time(time: str):
    if len(time) != 4 or not time.isdigit():
        raise Exception('Incorrect time format: {}'.format(time))
    return datetime.strptime(time, "%H%M").time() if time else None


def valid_uid(uid: str):
    uid = str(uid)
    return uid.isdigit() and len(uid) == 5