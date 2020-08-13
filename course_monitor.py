import os
import re
import sys
import argparse
from datetime import datetime

from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from notification_emitter import dispatch_emitters, SlackEmitter, ConsoleEmitter

wait_time = 180
debug = False


def d_print(msg):
    """Prints status messages only if debug flag is used"""
    if debug:
        print(msg)


def course_link_builder(sid: str, uid: str):
    return 'https://utdirect.utexas.edu/apps/registrar/course_schedule/{}/{}/' \
        .format(sid, uid)


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


def do_signin_seq(browser, usr_name: str, passwd: str) -> bool:
    if 'Sign in with your UT EID' in browser.title:
        heading = browser.find_element_by_xpath("//div[@id='message']/h1").text

        if 'Sign in with your UT EID' in heading:

            if usr_name and passwd:
                username_field = browser.find_element_by_id('username')
                username_field.clear()
                username_field.send_keys(usr_name)

                password_field = browser.find_element_by_id('password')
                password_field.clear()
                password_field.send_keys(passwd)

                signin_btn = browser.find_element_by_xpath("//input[@type='submit']")
                signin_btn.click()

        elif 'Multi-Factor Authentication Required' in heading:
            # todo click send push notification if it is not clicked or it timed out
            d_print('Please authorize on Duo')

    return 'UT Austin Registrar:' in browser.title and 'course search' in browser.title


def goto_page(browser, link: str, usr_name: str, passwd: str):
    d_print('browser going to {}'.format(link))

    browser.get(link)

    # wait until user logs in and the courses can be seen
    WebDriverWait(browser, sys.maxsize).until(lambda _: do_signin_seq(browser, usr_name, passwd))

    return browser


def goto_course_page(browser, sid: str, uid: str, usr_name: str, passwd: str):
    return goto_page(browser, course_link_builder(sid, uid), usr_name, passwd)


def goto_all_course_pages(browser, sid: str, uids: [str], usr_name: str, passwd: str) -> dict:
    curr_courses = {}
    for uid in uids:
        goto_course_page(browser, sid, uid, usr_name, passwd)
        curr_courses[uid] = parse_course(browser.page_source)

    return curr_courses


def parse_header(header: str) -> (str, str):
    """splits header text into its course code and name components"""
    header_matches = re.compile(r"([A-Z ]+)(\d{3}\w?) ([-\w' ]+)").match(header.strip())
    course_code = header_matches.group(1).strip() + ' ' + header_matches.group(2).strip()
    course_name = header_matches.group(3).strip()
    return course_code, course_name


def parse_course(browser_src: str) -> tuple:
    soup = BeautifulSoup(browser_src, 'html.parser')
    table = soup.find('table', {'id': 'details_table'})

    if table:
        row = table.find('tbody').find('tr')
        header = soup.find("section", {"id": "details"}).find("h2")
        course_code, _ = parse_header(header.text)
        # unique = row.find('td', {'data-th': 'Unique'}).text
        professor = row.find('td', {'data-th': 'Instructor'}).text
        status = row.find('td', {'data-th': 'Status'}).text
        return course_code, professor, status

    else:
        raise Exception("Current page does not contain any course information")


def changelist(p_courses: dict, c_courses: dict) -> dict:
    """Get a dict of changed courses with old and new statuses"""
    changed_courses = {}

    for uid, (code, prof, status) in c_courses.items():

        if uid in p_courses:
            (_, _, p_status) = p_courses[uid]

            if p_status != status:
                changed_courses[uid] = (code, prof, p_status, status)
        else:
            d_print('lost {} ({}) from refreshed course list'.format(code, uid))

    if len(changed_courses) > 0:
        d_print('list of courses that changed statuses')
        d_print(changed_courses)
    else:
        d_print('no change in courses')
    return changed_courses


def dispatch_onchange(prev_courses, curr_courses, emitters):
    if prev_courses:
        changed_courses = changelist(prev_courses, curr_courses)

        if len(changed_courses) > 0:
            dispatch_emitters(emitters, changed_courses)


def perform_course_checks():
    global prev_courses, curr_courses
    curr_courses = goto_all_course_pages(browser, sid, uids, usr_name, passwd)
    dispatch_onchange(prev_courses, curr_courses, emitters)
    prev_courses = curr_courses


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

    parser.add_argument('--debug', '-d',
                        default=False,
                        required=False,
                        action='store_true',
                        help='add this flag to see debug / status prints')

    parser.add_argument('--headless',
                        default=False,
                        required=False,
                        action='store_true',
                        help='add this flag to run Chrome in headless mode (no GUI available)')


def build_emitters(sem_id: str) -> []:
    emitters = [ConsoleEmitter()]
    if os.getenv('SLACK_TOKEN') and os.getenv('SLACK_CHANNEL_ID'):
        emitters.append(SlackEmitter(sem_id, os.getenv('SLACK_TOKEN'), os.getenv('SLACK_CHANNEL_ID')))

    return emitters


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monitor UT Course Schedule', allow_abbrev=True)
    add_args(parser)
    args = parser.parse_args()

    load_dotenv(os.path.join('./', '.env'))

    debug = args.debug is not None
    uids = [str(uid) for uid in args.uids]

    usr_name, passwd = (os.getenv('EID'), os.getenv('UT_PASS'))
    browser = init_browser(args.headless)

    sid = sem_code_builder(args.sem)
    emitters = build_emitters(sid)

    prev_courses, curr_courses = None, None

    scheduler = BackgroundScheduler(executors={'default': ThreadPoolExecutor(1)})
    scheduler.add_job(perform_course_checks, 'interval', seconds=wait_time, next_run_time=datetime.now())
    scheduler.start()
