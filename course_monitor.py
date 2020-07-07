import os
import sys
import time
import argparse
import random

from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

# from notification_emitter import ConsoleEmitter
from notification_emitter import SlackEmitter

# how long should selenium wait for an element to appear...
implicit_wait_time = 30
# random timer is customizable by setting the method and its parameters here
random_params = (30, 40)
random_time = random.randrange

debug = False


def d_print(msg):
    """Prints status messages only if debug flag is used"""
    if debug:
        print(msg)


def init_browser_link(link: str):
    """Starts browser and navigates to course schedule"""
    d_print('browser going to {} (you may need to sign in)'.format(link))

    driver = webdriver.Chrome()  # todo change this to support any browser
    driver.implicitly_wait(implicit_wait_time)
    driver.get(link)

    # wait for user logs in and the courses can be seen
    WebDriverWait(driver, sys.maxsize) \
        .until(lambda x: 'UT Austin Registrar:' in driver.title and 'course search' in driver.title)

    d_print('successfully entered course schedule')

    return driver


def parse_courses(driver) -> dict:
    """Parses page with Beautiful Soup and returns a dictionary with unique id as keys an (Course Title,
    Availability) tuple as value """

    courses = {}
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    table = soup.find('table', {'class': 'rwd-table results'})
    if table:
        table_body = table.find('tbody')

        rows = table_body.find_all('tr')

        curr_header = None
        for row in rows:
            # rows can only have header or the section information, but not both
            header = row.find('td', {'class': 'course_header'})
            unique = row.find('td', {'data-th': 'Unique'})
            status = row.find('td', {'data-th': 'Status'})

            if header:
                curr_header = header.text.strip()
            else:
                assert not header
                courses[unique.text] = (curr_header, status.text)
    else:
        d_print('did not find table in course schedule. What is going on?')

    d_print('here are the courses I found')
    d_print(courses)
    return courses


def click_next(driver) -> bool:
    """Returns true if a next button exists and was clicked, false otherwise"""

    success = False
    try:
        driver.implicitly_wait(0)
        driver.find_element_by_id('next_nav_link').click()
        success = True
    except NoSuchElementException:
        pass
    finally:
        driver.implicitly_wait(implicit_wait_time)

        d_print('found another page and clicking it!' if success else 'this is the last page of courses')
        return success


def filter_courses(courses: dict, uids: list) -> dict:
    """Returns subset of courses in courses that we are interested in"""

    if uids is None or len(uids) == 0:
        return courses

    filtered_courses = {}

    for uid in uids:
        if uid in courses:
            filtered_courses[uid] = courses[uid]

    d_print('we only care about courses with uids: {}'.format(uids))
    d_print('and the filtered list is {}'.format(filtered_courses))

    if len(filtered_courses) == 0:
        d_print('No course that we want has been found in course list. Are you sure you are on the right course page?')

    return filtered_courses


def changelist(p_courses: dict, c_courses: dict) -> dict:
    """Get a dict of changed courses with old and new statuses"""
    changed_courses = {}

    for uid, (name, status) in c_courses.items():

        if uid in p_courses:
            (p_name, p_status) = p_courses[uid]
            assert p_name == name
            if p_status != status:
                changed_courses[uid] = (name, p_status, status)
        else:
            d_print('lost {} ({}) from refreshed course list'.format(name, uid))

    if len(changed_courses) > 0:
        d_print('list of courses that changed statuses')
        d_print(changed_courses)
    else:
        d_print('no change in courses')
    return changed_courses


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monitor UT Course Schedule')
    parser.add_argument('-link',
                        metavar='<href>',
                        type=str,
                        required=True,
                        help='the url of the course schedule search results')

    parser.add_argument('--uid',
                        metavar='id',
                        type=int,
                        required=False,
                        nargs="+",
                        help='space separated list of the unique IDs of courses we are interested in searching')

    parser.add_argument('--debug',
                        required=False,
                        action='store_true',
                        help='add this flag to see debug / status prints')

    args = parser.parse_args()

    load_dotenv(os.path.join('./', '.env'))

    debug = args.debug is not None

    # emitter = ConsoleEmitter()
    emitter = SlackEmitter(os.getenv('SLACK_TOKEN'), os.getenv('SLACK_CHANNEL_ID'))

    browser = init_browser_link(args.link)

    uid = [str(uid) for uid in args.uid]

    prev_courses = None
    curr_courses = None

    # constant refresh loop
    while True:
        browser.get(args.link)
        curr_courses = {}

        # loop through all pages
        while True:
            curr_courses.update(parse_courses(browser))
            if not click_next(browser):
                break

        # only keep the courses we are interested in
        curr_courses = filter_courses(curr_courses, uid)

        if prev_courses:
            changed_courses = changelist(prev_courses, curr_courses)

            if len(changed_courses) > 0:
                emitter.emit_msg(changed_courses)

        prev_courses = curr_courses
        sleep_time = random_time(*random_params)
        d_print('going to sleep for {} seconds'.format(sleep_time))
        time.sleep(sleep_time)
