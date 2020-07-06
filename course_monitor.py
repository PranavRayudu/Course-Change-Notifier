import os
import sys
import time
import argparse

from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

implicit_wait_time = 30
sleep_time = 120  # todo randomize this


def init_browser_link(link):
    driver = webdriver.Chrome()  # todo change this to support any browser
    driver.implicitly_wait(implicit_wait_time)
    driver.get(link)

    # wait for user logs in and the courses can be seen
    WebDriverWait(driver, sys.maxsize) \
        .until(lambda x: 'UT Austin Registrar:' in driver.title and 'course search' in driver.title)

    return driver


def parse_courses(driver):
    """Parses page with Beautiful Soup and returns a dictionary with unique id as keys an (Course Title,
    Availability) tuple as value """

    course_list = {}
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
                curr_header = header
            else:
                assert not header
                course_list[unique] = (curr_header, status)

    return course_list


def filter_courses(course_list):
    """Returns subset of courses in course_list that we are interested in"""
    return course_list


def changelist(p_course_list, c_course_list):
    """Get a list of changed courses with old and new statuses"""
    change_list = {}

    for uid, (name, status) in c_course_list.items():

        if uid in p_course_list:
            (p_name, p_status) = p_course_list[uid]
            assert p_name == name
            if p_status != status:
                change_list[uid] = (name, p_status, status)
        else:
            print('lost {} ({}) from refreshed course list'.format(name, uid))

    return change_list


def click_next(driver):
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
        return success


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monitor UT Course Schedule')
    parser.add_argument('-link',
                        metavar='<href>',
                        required=True,
                        help='the link with the courses here')
    args = parser.parse_args()

    load_dotenv(os.path.join('./', '.env'))

    browser = init_browser_link(args.link)

    prev_course_list = None
    curr_course_list = None

    while True:
        browser.get(args.link)
        curr_course_list = {}

        while True:
            curr_course_list.update(parse_courses(browser))
            if not click_next(browser):
                break

        curr_course_list = filter_courses(curr_course_list)

        if prev_course_list:
            changed_courses = changelist(prev_course_list, curr_course_list)
            if len(changed_courses) > 0:

                for uid, (name, prev_status, new_status) in changed_courses:
                    pass  # todo send notification to user with link to register immediately if open?

        prev_course_list = curr_course_list
        time.sleep(sleep_time)
