import sys

from selenium.webdriver.support.wait import WebDriverWait

debug = False


def d_print(msg):
    """Prints status messages only if debug flag is used"""
    if debug:
        print(msg)


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

        return 'UT Austin Registrar:' in CourseMonitor.browser.title and \
               'course search' in CourseMonitor.browser.title

    @staticmethod
    def login(sid: str):
        CourseMonitor.__goto_page("https://utdirect.utexas.edu/apps/registrar/course_schedule/{}/".format(sid))

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
