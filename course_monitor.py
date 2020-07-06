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
    """Parses page with Beautiful Soup and returns a dictionary with unique id as keys an (Course Title, Instructor,
    Availability) tuple as value """
    return {}


def filter_courses(course_list):
    """Returns subset of courses in course_list that we are interested in"""
    return course_list


def changelist(prev_course_list, curr_course_list):
    """Get a list of changed courses"""
    # todo compare with desired course unique id's and see if anything changed from previous refresh?
    return curr_course_list


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
                pass  # todo emit a message saying courses changed

        prev_course_list = curr_course_list
        time.sleep(sleep_time)
