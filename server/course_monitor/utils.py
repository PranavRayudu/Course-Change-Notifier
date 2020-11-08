import os
import pytz
from datetime import datetime, timedelta, time

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from selenium import webdriver
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from server.course_monitor import Course, Monitor, ConsoleEmitter, SlackEmitter
from server.course_monitor.database import db

scheduler: BackgroundScheduler

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
    else:
        return webdriver.Chrome(options=options)


def load_courses():
    courses = db.session.query(Course).all()
    course_dict = {}
    for course in courses:
        course = Course(course.uid)
        course_dict[course.uid] = course

    # add_courses_to_jobs(scheduler, course_dict, times, jitter)
    return course_dict


def add_course(uid: str, commit=True):
    course = Course.get_course(uid)
    if not course:
        course = Course(uid=uid)
        db.session.add(course)
        if commit:
            db.session.commit()
    return course


def add_courses(uids: [str]) -> []:
    courses = []
    for uid in uids:
        courses.append(add_course(uid, commit=False))
    db.session.commit()
    return courses


def add_courses_to_jobs(courses: [], times: (None, None, 180), jitter=0) -> []:
    for course in courses:
        add_course_job(course, times, jitter)


def add_course_job(uid: str, times: tuple, jitter=0):

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

    course_check_id, course_start_id, course_end_id = Course.get_course_job_ids(uid)
    start_time, end_time, wait_time = times

    if added := is_time_between(start_time, end_time):
        # noinspection PyTypeChecker
        if not scheduler.get_job(course_check_id):
            scheduler.add_job(
                Course.check,
                'interval',
                args=(uid,),
                seconds=wait_time,
                next_run_time=datetime.now(),
                misfire_grace_time=None,
                id=course_check_id,
                jitter=jitter,
                coalesce=True)

        course = Course.get_course(uid)
        if course.paused:
            Course.pause_job(uid, scheduler)

    # if start_time and end_time:
    #     # start_date, end_date = get_today_times(start_time, end_time)
    #     start_date, end_date = next_datetime(start_time), next_datetime(end_time)
    #     if not scheduler.get_job(course_start_id):
    #         scheduler.add_job(
    #             add_course_job,
    #             trigger='date',
    #             args=(uid, times, jitter),
    #             id=course_start_id,
    #             run_date=start_date,)
    #     if added and not scheduler.get_job(course_end_id):
    #         scheduler.add_job(
    #             remove_course_job,
    #             args=(uid,),
    #             trigger='date',
    #             id=course_end_id,
    #             run_date=end_date)


def remove_all_courses():
    db.session.query(Course).delete()
    scheduler.remove_all_jobs()
    db.session.commit()


def remove_course(uid: str) -> Course:
    course = Course.get_course(uid)
    if course:
        Course.remove_jobs(uid, scheduler)
        db.session.query(Course).filter_by(uid=course.uid).delete()
        db.session.commit()
    return course


def remove_courses_from_jobs(courses: []):
    for course in courses:
        remove_course_job(course.uid)


def remove_course_job(uid: str):
    Course.remove_jobs(uid, scheduler)


def build_emitters(sem_id: str) -> []:
    emitters = [ConsoleEmitter()]
    token, channel = os.getenv('SLACK_TOKEN'), os.getenv('SLACK_CHANNEL')
    if token and channel:
        slack_emitter = SlackEmitter(sem_id, token, channel)
        emitters.append(slack_emitter)

    return emitters


def init_monitor(sem, usr_name, passwd, db_url, headless=False):
    browser = init_browser(headless)

    sid = build_sem_code(sem)
    emitters = build_emitters(sid)

    Course.Emitters = emitters

    Monitor.browser = browser
    Monitor.sid = sid
    Monitor.usr_name = usr_name
    Monitor.passwd = passwd

    global scheduler
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
