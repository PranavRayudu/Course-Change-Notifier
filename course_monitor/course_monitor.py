from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait

debug = False


def d_print(msg):
    """Prints status messages only if debug flag is used"""
    if debug:
        print(msg)


class CourseMonitor:
    browser, sid, usr_name, passwd = None, None, None, None
    login_fail = False

    @staticmethod
    def __course_link_builder(sid: str, uid: str):
        return 'https://utdirect.utexas.edu/apps/registrar/course_schedule/{}/{}/' \
            .format(sid, uid)

    @staticmethod
    def logged_in() -> bool:
        return 'UT Austin Registrar:' in CourseMonitor.browser.title and \
               'course search' in CourseMonitor.browser.title

    @staticmethod
    def __do_login_seq() -> bool:

        if CourseMonitor.login_fail:
            return False

        browser = CourseMonitor.browser
        if 'Sign in with your UT EID' in browser.title:

            heading = browser.find_element_by_xpath("//div[@id='message']/h1").text

            if 'Sign in with your UT EID' in heading:

                if CourseMonitor.usr_name and CourseMonitor.passwd:
                    username_field = browser.find_element_by_id('username')
                    username_field.clear()
                    username_field.send_keys(CourseMonitor.usr_name)

                    password_field = browser.find_element_by_id('password')
                    password_field.clear()
                    password_field.send_keys(CourseMonitor.passwd)

                    login_btn = browser.find_element_by_xpath("//input[@type='submit']")
                    login_btn.click()

            elif 'Multi-Factor Authentication Required' in heading:

                iframe = browser.find_element_by_id('duo_iframe')
                browser.switch_to.frame(iframe)
                messages = browser.find_elements_by_xpath(
                    "//div[@id='messages-view']"
                    "/div[@class='messages-list']"
                    "/div")

                push_active = False
                for message in messages:
                    if message.get_attribute('aria-hidden') == 'true':
                        continue
                    if 'info' in message.get_attribute('class'):
                        push_active = 'Pushed a login request to your device...' in message.text
                        break
                    if 'error' in message.get_attribute('class'):
                        CourseMonitor.login_fail = True
                        break

                if not push_active and not CourseMonitor.login_fail:

                    remember_me = browser.find_element_by_xpath(
                        "//div[@class='stay-logged-in']"
                        "/label[@class='remember_me_label_field']"
                        "/input[@type='checkbox']")

                    if not remember_me.is_selected():
                        remember_me.click()

                    # send push button
                    browser.find_element_by_xpath(
                        "(//button[contains(@class, 'auth-button')])[1]").click()

                browser.switch_to.default_content()

        return CourseMonitor.logged_in()

    @staticmethod
    def login():
        CourseMonitor.login_fail = False  # method acts as a reset for manual login
        CourseMonitor.__goto_page("https://utdirect.utexas.edu/apps/registrar/course_schedule/{}/"
                                  .format(CourseMonitor.sid))
        return CourseMonitor.logged_in()

    @staticmethod
    def __goto_page(link: str):
        d_print('browser going to {}'.format(link))
        CourseMonitor.browser.get(link)

        # wait until user logs in and the courses can be seen
        try:
            WebDriverWait(CourseMonitor.browser, timeout=60) \
                .until(lambda x: CourseMonitor.__do_login_seq())
        except TimeoutException:
            # fail login here and force manual login
            CourseMonitor.login_fail = True
        return CourseMonitor.browser

    @staticmethod
    def get_course_page(uid: str):
        if CourseMonitor.login_fail:
            return None
        return CourseMonitor.__goto_page(
            CourseMonitor.__course_link_builder(CourseMonitor.sid, uid)).page_source
