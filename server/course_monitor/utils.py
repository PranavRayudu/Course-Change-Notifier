import os
import pytz
from datetime import datetime, timedelta, time

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from selenium import webdriver
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from server.course_monitor import Course, Monitor, ConsoleEmitter, SlackEmitter


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


def load_courses(emitters: [], db):
    courses = db.session.query(Course).all()
    course_dict = {}
    for course in courses:
        course = Course(course.uid, emitters)
        course_dict[course.uid] = course

    # add_courses_to_jobs(scheduler, course_dict, times, jitter)
    return course_dict


def add_course(uid: str, emitters: [], courses, db, commit=True):
    if uid not in courses:
        course = Course(uid=uid, emitters=emitters)
        db.session.add(course)
        if commit:
            db.session.commit()
        courses[uid] = course
        return course


def add_courses(uids: [str], emitters: [], db) -> {}:
    courses = {}
    for uid in uids:
        add_course(uid, emitters, courses, db)
    db.session.commit()
    return courses


def add_courses_to_jobs(scheduler: BackgroundScheduler, courses: {}, times: (None, None, 180), jitter=0) -> []:
    for course in courses.values():
        add_course_job(scheduler, course, times, jitter)


def add_course_job(scheduler: BackgroundScheduler, course: Course, times: tuple, jitter=0):

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

    course_check_id, course_start_id, course_end_id = course.get_course_job_ids()
    start_time, end_time, wait_time = times

    if added := is_time_between(start_time, end_time):
        # noinspection PyTypeChecker
        scheduler.add_job(
            course.check,
            'interval',
            seconds=wait_time,
            next_run_time=datetime.now(),
            misfire_grace_time=None,
            id=course_check_id,
            jitter=jitter,
            coalesce=True)
        if course.paused:
            course.pause_job(scheduler)

    if start_time and end_time:
        # start_date, end_date = get_today_times(start_time, end_time)
        start_date, end_date = next_datetime(start_time), next_datetime(end_time)
        scheduler.add_job(
            add_course_job,
            trigger='date',
            args=(scheduler, course, times, jitter),
            id=course_start_id,
            run_date=start_date)
        if added:
            scheduler.add_job(
                remove_course_job,
                args=(scheduler, course),
                trigger='date',
                id=course_end_id,
                run_date=end_date)


def remove_courses(scheduler, courses: {}, db):
    for uid in list(courses.keys()):
        remove_course(uid, courses, scheduler, db)


def remove_course(uid: str, courses: {}, scheduler, db) -> Course:
    if uid in courses:
        course = courses.pop(uid)
        remove_course_job(scheduler, course)
        db.session.query(Course).filter_by(uid=course.uid).delete()
        db.session.commit()
        return course


def remove_courses_from_jobs(scheduler, courses: {}):
    for course in courses.values():
        remove_course_job(scheduler, course)


def remove_course_job(scheduler: BackgroundScheduler, course: Course):
    course.remove_jobs(scheduler)


def build_emitters(sem_id: str) -> []:
    emitters = [ConsoleEmitter()]
    token, channel = os.getenv('SLACK_TOKEN'), os.getenv('SLACK_CHANNEL')
    if token and channel:
        emitters.append(SlackEmitter(sem_id, token, channel))

    return emitters


def init_monitor(sem, usr_name, passwd, db_url, headless=False):
    browser = init_browser(headless)

    sid = build_sem_code(sem)
    emitters = build_emitters(sid)

    Monitor.browser = browser
    Monitor.sid = sid
    Monitor.usr_name = usr_name
    Monitor.passwd = passwd

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.configure(executors={'default': ThreadPoolExecutor(1)},
                        jobstores={'default': SQLAlchemyJobStore(db_url)},  # jobs persist on restarts
                        timezone=pytz.timezone('US/Central'))
    # scheduler.add_job(CourseMonitor.login, id=str(sid))
    # CourseMonitor.login()  # login pre-emptively before getting all course information

    return scheduler, emitters


def get_time(time: str):
    if len(time) != 4 or not time.isdigit():
        raise Exception('Incorrect time format: {}'.format(time))
    # convert from CST to UTC time
    return datetime.strptime(time, "%H%M").time() if time else None


def valid_uid(uid: str):
    uid = str(uid)
    return uid.isdigit() and len(uid) == 5
