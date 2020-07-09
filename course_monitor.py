import os
import sys
import time
import random
import argparse

from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from notification_emitter import SlackEmitter  # , ConsoleEmitter

# random timer is customizable by setting the method and its parameters here
random_time = random.randrange
random_params = (180, 300)  # wait 3-5 min

debug = False


def d_print(msg):
    """Prints status messages only if debug flag is used"""
    if debug:
        print(msg)


def do_signin_seq(browser, usr_name: str, passwd: str) -> bool:
    if 'Sign in with your UT EID' in browser.title:
        heading = browser.find_element_by_xpath("//div[@id='message']/h1").text

        if 'Sign in with your UT EID' in heading:
            username_field = browser.find_element_by_id('username')
            username_field.clear()
            username_field.send_keys(usr_name)

            password_field = browser.find_element_by_id('password')
            password_field.clear()
            password_field.send_keys(passwd)

            signin_btn = browser.find_element_by_xpath("//input[@type='submit']")
            signin_btn.click()

        elif 'Multi-Factor Authentication Required' in heading:
            # todo click send push notification if it is not clicked or it timed out... does Duo allow that?
            d_print('Please authorize on Duo')

    return 'UT Austin Registrar:' in browser.title and 'course search' in browser.title


def goto_course_page(browser, link: str, usr_name: str, passwd: str):
    d_print('browser going to {} (you may need to sign in)'.format(link))

    browser.get(link)

    # wait until user logs in and the courses can be seen
    WebDriverWait(browser, sys.maxsize).until(lambda _: do_signin_seq(browser, usr_name, passwd))

    d_print('successfully entered course schedule')

    return browser


def parse_courses(browser) -> dict:
    """Parses page with Beautiful Soup and returns a dictionary with unique id as keys an (Course Title,
    Availability) tuple as value """

    courses = {}
    soup = BeautifulSoup(browser.page_source, 'html.parser')
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


def click_next(browser) -> bool:
    """Returns true if a next button exists and was clicked, false otherwise"""

    try:
        browser.find_element_by_id('next_nav_link').click()
        d_print('found another page and clicking it!')
        return True
    except NoSuchElementException:
        pass

    d_print('this is the last page of courses')
    return False


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
    parser = argparse.ArgumentParser(description='Monitor UT Course Schedule', allow_abbrev=True)
    parser.add_argument('--link', '-l',
                        metavar='<href>',
                        type=str,
                        required=True,
                        help='the url of the course schedule search results')

    parser.add_argument('--uid', '-u',
                        metavar='id',
                        type=int,
                        nargs="+",
                        default=[],
                        required=False,
                        help='space separated list of the unique IDs of courses we are interested in searching')

    parser.add_argument('--debug', '-d',
                        default=False,
                        required=False,
                        action='store_true',
                        help='add this flag to see debug / status prints')

    args = parser.parse_args()

    load_dotenv(os.path.join('./', '.env'))

    debug = args.debug is not None

    # emitter = ConsoleEmitter()
    usr_name, passwd = (os.getenv('EID'), os.getenv('UT_PASS'))
    browser = goto_course_page(webdriver.Chrome(), args.link, usr_name, passwd)

    soup = BeautifulSoup(browser.page_source, 'html.parser')
    semester_id = soup.find('input', {'name': 'ccyys', 'type': 'hidden'}).get('value')

    emitter = SlackEmitter(semester_id, os.getenv('SLACK_TOKEN'), os.getenv('SLACK_CHANNEL_ID'))

    uid = [str(uid) for uid in args.uid]

    prev_courses = None
    curr_courses = None

    # constant refresh loop
    while True:

        goto_course_page(browser, args.link, usr_name, passwd)
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
                emitter.emit(changed_courses)

        prev_courses = curr_courses
        sleep_time = random_time(*random_params)
        d_print('going to sleep for {} seconds'.format(sleep_time))
        time.sleep(sleep_time)
