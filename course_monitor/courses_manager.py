import os
from datetime import datetime

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from selenium import webdriver

from course_monitor.course import Course
from course_monitor.course_monitor import CourseMonitor
from course_monitor.notification_emitter import ConsoleEmitter, SlackEmitter


def build_sem_code(sem: str):
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
    for uid in list(courses.keys()):
        remove_course(uid, courses)


def remove_course(uid: str, courses: {}):
    if uid in courses:
        remove_course_job(courses.pop(uid))


def remove_courses_from_jobs(courses: {}):
    for course in courses.values():
        remove_course_job(course)


def remove_course_job(course: Course):
    if course.job:
        course.job.remove()


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

    CourseMonitor.browser = browser
    CourseMonitor.sid = sid
    CourseMonitor.usr_name = usr_name
    CourseMonitor.passwd = passwd

    scheduler = BackgroundScheduler(daemon=True, executors={'default': ThreadPoolExecutor(1)})
    # scheduler.add_job(CourseMonitor.login, id=str(sid))
    CourseMonitor.login()  # login pre-emptively before getting all course information

    return scheduler, emitters


def get_time(time: str):
    return datetime.strptime(time, "%H%M").time() if time else None
