import re
import sys
from bs4 import BeautifulSoup

from selenium.webdriver.support.wait import WebDriverWait

debug = True


def d_print(msg):
    """Prints status messages only if debug flag is used"""
    if debug:
        print(msg)


class Course:

    def __init__(self, uid: str, emitters: []):
        self.uid = uid
        self.emitters = emitters
        self.prev_course, self.cur_course = None, None

    @staticmethod
    def __parse_header(header: str) -> (str, str):
        """splits header text into its course code and name components"""
        header_matches = re.compile(r"([A-Z ]+)(\d{3}\w?) ([-\w' ]+)").match(header.strip())
        course_code = header_matches.group(1).strip() + ' ' + header_matches.group(2).strip()
        course_name = header_matches.group(3).strip()
        return course_code, course_name

    def __parse_course(self, browser_src: str) -> tuple:
        soup = BeautifulSoup(browser_src, 'html.parser')
        table = soup.find('table', {'id': 'details_table'})

        if table:
            row = table.find('tbody').find('tr')
            header = soup.find("section", {"id": "details"}).find("h2")
            course_code, _ = self.__parse_header(header.text)
            # unique = row.find('td', {'data-th': 'Unique'}).text
            professor = row.find('td', {'data-th': 'Instructor'}).text
            status = row.find('td', {'data-th': 'Status'}).text
            return course_code, professor, status

        else:
            raise Exception("Current page does not contain any course information")

    def __changes(self) -> dict:
        """Get a dict of changed courses with old and new statuses"""
        changed_course = {}

        (code, prof, status) = self.cur_course

        (_, _, p_status) = self.prev_course

        if p_status != status:
            changed_course[self.uid] = (code, prof, p_status, status)

        if len(changed_course) > 0:
            d_print('{} that changed status'.format(changed_course))
        else:
            d_print('no change in course {}'.format(self.uid))
        return changed_course

    def __dispatch_emitters(self, changes: dict):
        """send class change message on every emitter in emitters"""
        if len(changes) == 0:
            return

        for emitter in self.emitters:
            emitter.emit(changes)

    def do_check(self):
        self.cur_course = self.__parse_course(CourseMonitor.get_course_page(self.uid))
        if self.prev_course:
            self.__dispatch_emitters(self.__changes())
        self.prev_course = self.cur_course


class CourseMonitor:
    browser, sid, usr_name, passwd = None, None, None, None

    @staticmethod
    def __course_link_builder(sid: str, uid: str):
        return 'https://utdirect.utexas.edu/apps/registrar/course_schedule/{}/{}/' \
            .format(sid, uid)

    @staticmethod
    def __do_login_seq() -> bool:
        if 'Sign in with your UT EID' in CourseMonitor.browser.title:
            heading = CourseMonitor.browser.find_element_by_xpath("//div[@id='message']/h1").text

            if 'Sign in with your UT EID' in heading:

                if CourseMonitor.usr_name and CourseMonitor.passwd:
                    username_field = CourseMonitor.browser.find_element_by_id('username')
                    username_field.clear()
                    username_field.send_keys(CourseMonitor.usr_name)

                    password_field = CourseMonitor.browser.find_element_by_id('password')
                    password_field.clear()
                    password_field.send_keys(CourseMonitor.passwd)

                    login_btn = CourseMonitor.browser.find_element_by_xpath("//input[@type='submit']")
                    login_btn.click()

            elif 'Multi-Factor Authentication Required' in heading:
                # todo click send push notification if it is not clicked or it timed out
                d_print('Please authorize on Duo')

        return 'UT Austin Registrar:' in CourseMonitor.browser.title and\
               'course search' in CourseMonitor.browser.title

    @staticmethod
    def __goto_page(link: str):
        d_print('browser going to {}'.format(link))

        CourseMonitor.browser.get(link)

        # wait until user logs in and the courses can be seen
        WebDriverWait(CourseMonitor.browser, sys.maxsize).until(lambda x: CourseMonitor.__do_login_seq())

        return CourseMonitor.browser

    @staticmethod
    def get_course_page(uid: str):
        return CourseMonitor.__goto_page(CourseMonitor.__course_link_builder(CourseMonitor.sid, uid)).page_source
